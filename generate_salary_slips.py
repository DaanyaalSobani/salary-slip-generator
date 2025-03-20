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
    
    # Get position from the second column
    # First try the unnamed column, then try Position if it exists
    position = ''
    if 'Unnamed: 1' in employee and not pd.isna(employee['Unnamed: 1']):
        position = str(employee['Unnamed: 1']).strip()
    elif 'Position' in employee and not pd.isna(employee['Position']):
        position = str(employee['Position']).strip()
    employee['Position'] = position
    
    # Clean up field names
    employee['Days_Worked'] = employee.get('Days Worked', 0)
    employee['Net_Pay'] = employee.get('Net Pay', 0)
    employee['Previous_Loan_Balance'] = employee.get('Previous Loan Balance', 0)
    employee['Current_Loan_Balance'] = employee.get('Current Loan balance', 0)
    
    # Handle Comment field - convert nan to empty string
    employee['Comment'] = '' if pd.isna(employee.get('Comment')) else str(employee.get('Comment'))
    
    # Add computed fields
    try:
        deductions = employee.get('Deductions', 0)
        if pd.isna(deductions) or str(deductions).strip() == '':
            deductions = 0
        elif isinstance(deductions, str):
            deductions = float(deductions.replace(',', ''))
        
        employee['has_deductions'] = deductions > 0
    except (ValueError, TypeError):
        employee['has_deductions'] = False
        
    return employee

def generate_salary_slips(csv_file):
    """Generate HTML salary slips from CSV data"""
    try:
        print(f"Reading CSV file: {csv_file}")
        
        # Read the CSV file without headers first
        df = pd.read_csv(csv_file, header=None, encoding='utf-8')
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
        
        # Extract the payroll section and set proper column names
        header_row = df.iloc[payroll_start]
        payroll_data = df.iloc[payroll_start + 1:].copy()  # Get data after header
        
        # Clean up column names and handle the position column
        column_names = []
        for i, col in enumerate(header_row):
            if i == 1:  # Second column is position
                column_names.append('Position')
            elif pd.isna(col):
                column_names.append(f'Unnamed: {i}')
            else:
                column_names.append(col)
        payroll_data.columns = column_names
        
        # Process employees
        employees = []
        in_business_section = False
        
        for idx, row in payroll_data.iterrows():
            try:
                # Check if we're entering the business section
                if isinstance(row['Name'], str) and row['Name'].strip().lower() == 'business':
                    in_business_section = True
                    continue
                
                # Check if we're entering a non-payroll section
                if isinstance(row['Name'], str) and row['Name'].strip().lower() in ['donation', 'expenses']:
                    break
                
                # Skip empty rows and section headers
                if pd.isna(row['Name']) or str(row['Name']).strip().lower() in ['payroll', 'personal']:
                    continue
                
                # Check if this is a valid employee row (has salary)
                salary = row.get('Salary', '')
                if pd.isna(salary) or str(salary).strip() == '':
                    continue
                    
                print(f"Processing row for employee: {row['Name']} ({'Business' if in_business_section else 'Personal'})")
                employee = process_employee_data(row)
                employees.append(employee)
                
            except Exception as row_error:
                print(f"Warning: Error processing row {idx}: {str(row_error)}")
                continue
        
        if not employees:
            raise Exception("No salary slips were generated")
        
        print(f"Successfully processed {len(employees)} employees")
        
        # Set up Jinja2 environment
        env = Environment(loader=FileSystemLoader('templates'))
        # Add custom filters
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
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