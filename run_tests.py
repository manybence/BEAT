import datetime
import os

# Generate today's date in YYYY_MM_DD format
today = datetime.datetime.today().strftime('%Y_%m_%d')

# Define report filename inside "test" folder
report_file = f"test/reports/report_{today}.html"

# Run pytest with the generated filename
os.system(f"pytest --html={report_file} --self-contained-html")

input("Press any button to exit.")