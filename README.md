# Salary Slip Generator

A Docker-based web application that generates professional salary slips from CSV data. The application provides a simple interface for uploading CSV files and generates printable salary slips for all employees.

![Home Page](docs/images/home-page.png)

## Features

- Simple web interface for CSV upload
- Automatic salary slip generation
- Support for multiple currencies
- Handles loan and deduction calculations
- Print-friendly output
- Docker containerization for easy deployment

## Quick Start

1. Install Docker and Docker Compose
2. Clone this repository
3. Run the application:
   ```bash
   docker-compose up --build
   ```
4. Access the application at http://localhost:5000

![Upload Interface](docs/images/upload-interface.png)

## CSV File Structure

The application expects a specific CSV format. Here's a detailed breakdown:

### Required Structure

```csv
Payroll,,,,,,,,,,,,
Name,Position,Salary,Days Worked,Deductions,Net Pay,Currency,Method,Account,Previous Loan Balance,Current Loan balance,Comment,Status
Personal,,,,,,,,,,,,
John Doe,Manager,"50,000.00",30,"5,000.00","45,000.00",PKR,Bank Transfer,HBML-001,"10,000.00","5,000.00",Loan payment,
```

### Column Descriptions

| Column Name | Description | Required | Format | Example |
|------------|-------------|----------|--------|---------|
| Name | Employee's full name | Yes | Text | John Doe |
| Position | Job title/role | No | Text | Manager |
| Salary | Base salary | Yes | Number with optional commas | "50,000.00" |
| Days Worked | Number of days worked | Yes | Number | 30 |
| Deductions | Total deductions | No | Number with optional commas | "5,000.00" |
| Net Pay | Final salary after deductions | Yes | Number with optional commas | "45,000.00" |
| Currency | Currency code | No (defaults to PKR) | Text | PKR |
| Method | Payment method | No | Text | Bank Transfer |
| Account | Bank account or reference | No | Text | HBML-001 |
| Previous Loan Balance | Previous loan amount | No | Number with optional commas | "10,000.00" |
| Current Loan balance | Current loan amount | No | Number with optional commas | "5,000.00" |
| Comment | Additional notes | No | Text | Loan payment |
| Status | Payment status | No | Text | Paid |

### CSV File Example

Here's a complete example of a valid CSV file:

```csv
Payroll,,,,,,,,,,,,
Name,Position,Salary,Days Worked,Deductions,Net Pay,Currency,Method,Account,Previous Loan Balance,Current Loan balance,Comment,Status
Personal,,,,,,,,,,,,
John Doe,Manager,"50,000.00",30,"5,000.00","45,000.00",PKR,Bank Transfer,HBML-001,"10,000.00","5,000.00",Loan payment,
Jane Smith,Developer,"45,000.00",30,0.00,"45,000.00",PKR,Bank Transfer,HBML-002,,,No deductions,
Business,,,,,,,,,,,,
Alice Johnson,CEO,"150,000.00",30,"15,000.00","135,000.00",PKR,RAAST,HBML-003,"30,000.00","15,000.00",Monthly loan deduction,
```

### Important Notes

1. The CSV file must start with the "Payroll" header row
2. The second row must contain the column headers
3. Sections can be divided using "Personal" and "Business" rows
4. Numbers can include commas for thousands (e.g., "50,000.00")
5. Empty cells are allowed for optional fields

![Generated Salary Slip](docs/images/salary-slip.png)

## Generated Output

The application generates professional salary slips with the following features:

- Company header and salary slip title
- Employee details section
- Payment information
- Salary breakdown
- Loan/deduction details (if applicable)
- Signature spaces
- Print-friendly formatting

## Development

To run the application in development mode:

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask application:
   ```bash
   python app.py
   ```

## Docker Configuration

The application includes:
- Dockerfile for containerization
- docker-compose.yml for easy deployment
- Volume mapping for persistent storage
- Development mode configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 