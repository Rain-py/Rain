import json
from bs4 import BeautifulSoup


def read_html_table(path):
    # Read the HTML file
    with open(path, 'r') as file:
        html_data = file.read()

    # Parse the HTML
    soup = BeautifulSoup(html_data, 'html.parser')

    # Find the table element
    table = soup.find('table')

    # Initialize an empty list for table data
    table_data = []

    # Extract table headers
    headers = [header.get_text() for header in table.find_all('th')]

    # Extract table rows
    rows = table.find_all('tr')

    # Iterate over rows
    for row in rows:
        row_data = []
        cells = row.find_all('td')

        # Iterate over cells in the row
        for cell in cells:
            row_data.append(cell.get_text())

        # Add the row data to the table data list
        table_data.append(row_data)
    return headers, table_data

def create_csv_from_table(headers, table_data):
    # Create a dictionary to hold the table data
    data_dict = {
        'headers': headers[:6],
        'rows': table_data[1:]  # Exclude the header row
    }

    # convert the dictionary into as csv format
    csv_data = ''
    for header in data_dict['headers']:
        csv_data += header + ','
    csv_data = csv_data[:-1] + '\n'
    for row in data_dict['rows']:
        for i in range(len(data_dict['headers'])):
            csv_data += row[i] + ','
        csv_data = csv_data[:-1] + '\n'
    return csv_data

if __name__ == '__main__':
    headers, table_data = read_html_table('price.html')
    csv_data = create_csv_from_table(headers, table_data)
    # save the csv data into a file
    with open('price.csv', 'w') as file:
        file.write(csv_data)

