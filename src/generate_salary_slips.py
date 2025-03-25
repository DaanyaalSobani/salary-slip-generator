import os
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader

def format_currency(amount, currency="PKR"):
    """Format currency values with thousand separators"""
    try:
        # Handle NaN values
        if pd.isna(amount):
            return "0.00"
        # Remove any existing commas and convert to float
        if isinstance(amount, str):
            amount = float(amount.replace(",", ""))
        return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return "0.00"

def process_employee_data(employee):
    """Process employee data and add computed fields"""
    # Convert row to dictionary if it's a pandas Series
    if isinstance(employee, pd.Series):
        employee = employee.to_dict()
    
    # Helper function to handle empty/nan values
    def clean_value(value, default_value='', is_numeric=False):
        if pd.isna(value) or str(value).strip() == '':
            return 0 if is_numeric else default_value
        return value

    # Required fields with default values
    processed_data = {
        'Name': clean_value(employee.get('Name')),
        'Position': clean_value(employee.get('Position')),
        'Days_Worked': clean_value(employee.get('Days Worked'), 0, True),
        'Salary': clean_value(employee.get('Salary'), 0, True),
        'Deductions': clean_value(employee.get('Deductions'), 0, True),
        'Net_Pay': clean_value(employee.get('Net Pay'), 0, True),
        'Previous_Loan_Balance': clean_value(employee.get('Previous Loan Balance'), 0, True),
        'Current_Loan_Balance': clean_value(employee.get('Current Loan Balance'), 0, True),
        'Currency': clean_value(employee.get('Currency'), 'PKR'),
        'Method': clean_value(employee.get('Method')),
        'Account': clean_value(employee.get('Account')),
        'Comment': clean_value(employee.get('Comment'))
    }
    
    # Get position from the second column
    # First try the unnamed column, then try Position if it exists
    if 'Unnamed: 1' in employee and not pd.isna(employee['Unnamed: 1']):
        processed_data['Position'] = str(employee['Unnamed: 1']).strip()
    elif 'Position' in employee and not pd.isna(employee['Position']):
        processed_data['Position'] = str(employee['Position']).strip()
    
    # Add computed fields
    try:
        deductions = processed_data['Deductions']
        if isinstance(deductions, str):
            deductions = float(deductions.replace(',', ''))
        processed_data['has_deductions'] = deductions > 0
    except (ValueError, TypeError):
        processed_data['has_deductions'] = False
        
    return processed_data

def generate_salary_slips(csv_file):
    """Generate HTML salary slips from CSV data"""
    try:
        print(f"Reading CSV file: {csv_file}")
        
        # Read the CSV file without headers first and allow any number of columns
        df = pd.read_csv(csv_file, header=None, encoding='utf-8', on_bad_lines='skip')
        print("CSV data loaded, searching for payroll section...")
        
        # Find the payroll section start (row that contains "Name" in first column)
        payroll_start = None
        for idx, row in df.iterrows():
            if isinstance(row[0], str) and row[0].strip() == 'Name':
                payroll_start = idx
                break
        
        if payroll_start is None:
            raise Exception("Could not find payroll header (row starting with 'Name') in CSV file")
            
        print(f"Found payroll header at row {payroll_start}")
        
        # Extract the payroll section
        payroll_data = df.iloc[payroll_start + 1:].copy()  # Get data after header
        header_row = df.iloc[payroll_start]
        
        # Map the essential columns we need
        column_mapping = {}
        required_columns = ['Name', 'Position', 'Days Worked', 'Salary', 'Deductions', 'Net Pay', 
                          'Previous Loan Balance', 'Current Loan Balance', 'Currency', 'Method', 'Account', 'Comment']
        
        # Create case-insensitive lookup dictionary
        required_columns_lower = {col.lower(): col for col in required_columns}
        
        # Find the column indices for our required fields
        for i, col in enumerate(header_row):
            if pd.isna(col):
                continue
            col_name = str(col).strip()
            col_name_lower = col_name.lower()
            if col_name_lower in required_columns_lower:
                column_mapping[i] = required_columns_lower[col_name_lower]
            elif i == 1 and 'position' not in column_mapping.values():  # Special case for position in second column
                column_mapping[i] = 'Position'
        
        # Rename columns we care about and drop others
        new_columns = {}
        for i in range(len(payroll_data.columns)):
            if i in column_mapping:
                new_columns[i] = column_mapping[i]
            else:
                new_columns[i] = f'Unused_{i}'
        payroll_data.columns = [new_columns[i] for i in range(len(payroll_data.columns))]
        
        # Keep only the columns we need
        columns_to_keep = [col for col in payroll_data.columns if not col.startswith('Unused_')]
        payroll_data = payroll_data[columns_to_keep]
        
        # Process employees
        employees = []
        in_business_section = False
        
        for idx, row in payroll_data.iterrows():
            try:
                # Check if we're entering the business section
                name_value = row.get('Name', '')
                if pd.isna(name_value):
                    continue
                    
                name_value = str(name_value).strip().lower()
                if name_value == 'business':
                    in_business_section = True
                    continue
                
                # Check if we're entering a non-payroll section
                if name_value in ['donation', 'expenses']:
                    break
                
                # Skip section headers
                if name_value in ['payroll', 'personal']:
                    continue
                
                # Check if this is a valid employee row (has salary)
                salary = row.get('Salary', '')
                if pd.isna(salary) or str(salary).strip() == '':
                    continue
                    
                print(f"Processing row for employee: {row.get('Name', '')} ({'Business' if in_business_section else 'Personal'})")
                employee = process_employee_data(row)
                employees.append(employee)
                
            except Exception as row_error:
                print(f"Warning: Error processing row {idx}: {str(row_error)}")
                continue
        
        if not employees:
            raise Exception("No salary slips were generated")
        
        print(f"Successfully processed {len(employees)} employees")
        
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        env.filters['format_currency'] = format_currency
        
        # Get the template
        template = env.get_template('salary_slips.html')
        
        # Render the template
        html_content = template.render(
            employees=employees,
            month_year=datetime.now().strftime("%B %Y")
        )
        
        return html_content
    
    except Exception as e:
        error_message = f"Error processing CSV file: {str(e)}"
        print(error_message)
        return f'<div style="color: red;">{error_message}</div>'

def main():
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(f"Current directory: {current_dir}")
        
        # Input and output file paths
        csv_file = os.path.join(current_dir, 'Reference', 'Monthend Payments - Month End March 2025.csv')
        output_file = os.path.join(current_dir, 'generated_salary_slips.html')
        
        print(f"CSV file path: {csv_file}")
        print(f"Output file path: {output_file}")
        
        # Check if CSV file exists
        if not os.path.exists(csv_file):
            raise Exception(f"CSV file not found at: {csv_file}")
        
        # Generate the salary slips
        html_content = generate_salary_slips(csv_file)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Salary slips have been generated and saved to: {output_file}")
    
    except Exception as e:
        print(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main() 