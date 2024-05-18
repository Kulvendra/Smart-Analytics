

Using Assitant =>

calling uploadFile() to upload a file and returning an FILE ID.

calling createAssistant() to create an assistant with an instruction to be an data analyst who generates charts using input data and returning an ASSISTANT ID.

calling createThread() with prompt that contains project description and format of the chart mapping data with header fields with FILE ID and returning the THREAD ID.

at last calling runPrompt() with THREAD ID and ASSISTANT ID to run the prompt query and get the response.

sample output => [{'x': 'Matter Number', 'y': 'Total Fees', 'type': 'bar'}, {'x': 'Vendor Name', 'y': 'Invoice Total', 'type': 'bar'}, {'x': 'Invoice Date', 'y': 'Total Fees', 'type': 'line'}, {'x': 'Billing Start Date', 'y': 'Total Fees', 'type': 'line'}, {'x': 'Billing End Date', 'y': 'Invoice Total', 'type': 'line'}, {'x': 'Legal Entity', 'y': 'Total Fees', 'type': 'bar'}, {'x': 'Matter Name', 'y': 'Invoice Total', 'type': 'bar'}, {'x': 'Matter Number', 'y': 'Total Expense', 'type': 'bar'}, {'x': 'Vendor Name', 'y': 'Total Expense', 'type': 'bar'}]

Now sending this data to an python script that generate ECHART config using above input and that will return as list of json object where each object is an ECHART CONFIG using the complete xlsx data 

sample output => 

[{
        "xAxis": {
            "type": "category",
            "data": [
                "MHAI",
                "MHAI",
                "MHAI",
                "MHAI"
            ],
            "name": "Matter Number"
        },
        "yAxis": {
            "type": "value",
            "name": "Total Fees"
        },
        "series": [
            {
                "data": [
                    564300.0,
                    564300.0,
                    564300.0,
                    564300.0
                ],
                "type": "bar"
            }
        ],
        "tooltip": {
            "trigger": "axis"
        },
        "title": {
            "text": "Total Fees vs Matter Number"
        }
    }]