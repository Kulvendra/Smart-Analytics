from openai import OpenAI
import time
import json
import os
import time
import re

client = OpenAI(api_key=OPENAI_API_KEY)
def uploadFile(filePath):
    file = client.files.create(
        file=open(filePath, "rb"),
        purpose="assistants"
    )
    return file.id
def createAssistant():
    assistant = client.beta.assistants.create(
        name="Chart Creator",
        instructions="You are a data analyst. Write and run the function to generate charts",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4-turbo",
    )
    return assistant.id
def createThread(prompt,file_id):
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
                "attachments": [
                    {
                    "file_id": file_id,
                    "tools": [{"type": "code_interpreter"}]
                    }
                ]
            }]
    )
    return thread.id
def runPrompt(threadId,assistantId):
    run = client.beta.threads.runs.create(
        thread_id=threadId,
        assistant_id=assistantId,
        )
    return run.id
def check_run_status(client, thread_id, run_id):
    while True:
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run.status == 'completed':
            print("Run completed!")
            return True
        elif run.status == 'failed':
            print("Run failed.")
            break
        else:
            print("Run is still in progress...")
            time.sleep(5)  # Wait for 5 seconds before checking again
def startChat(filepath,prompt):
    fileId = uploadFile(filepath)
    assistantId = createAssistant()
    threadId = createThread(prompt,fileId)
    runId = runPrompt(threadId,assistantId)
    if status := check_run_status(client, threadId, runId):
        messages = client.beta.threads.messages.list(
                thread_id=threadId
            )
        # print("==================")
        # print(messages)
        # print("==================")
        text=messages.data[0].content[0].text.value
        # print("text => ",text)
        pattern = r'```json\s+(.*?)\s+```'
        matches = re.findall(pattern, text, re.DOTALL)
        data = matches[0].replace('\n', '').replace("'", '"')
        json_object = json.loads(data)
        print(json_object)
file = "test.xlsx"
prompt = '''
Project Description :
The project is related to invoice and matter data. It should address the following use cases or functionalities
1. Ability to summarize key facts, issues and current status of specific matters
2. Based on current status and complexity of a matter, estimate the potential legal costs and timeline to resolution.
3. Provide a range of expected legal fees for specific matter types
4. Identify potential risks with specific matters
5. Provide document summaries
6. Draft documents based on templates and known facts about the matter
7. Review data produced in discovery and identify relevant information
8. Provide proposed timelines and milestones for a matter
9. Identify any outlier or unusual timekeeper rates charged by a firm across matter types/timekeeper levels
10. Calculate average hourly rate charged by each firm by matter type for time period
11. Breakdown legal spend by matter, by timekeeper, by firm for time period
12. Identify matters/firms that are close to exceeding budget or have exceeded budget
13. Identify firms routinely exceeding the matter budget
14. Analyze legal spend trends
15. Forecast legal spend based on current historical data
16. Provide range of estimated legal spend for a specific matter type based on specific timekeeper rates and billing trends.
17. Evaluate the efficiency and cost-effectiveness of firms in handling specific matters/matter types based on timekeeper rates, staffing and overall spend
18. Compare performance metrics of firms
19. Suggest strategies to optimize legal spend with a firm while maintaining quality and effectiveness.
1 => Analyse the project description given above and fist prepare a list of chart that can be preapared for this description 
2 => Now on the basic of above generated list  read the xlsx file and columns as fields ,  Generate the unique 2D chart combination between fields
4 => x-axis and y-axis combination should be unique 
5 => generated should be relavent as per the project and according to the description
6=> each combination should have a chart type from one of the bar,line and column and once any x and y combination in pushed in the list that combination can not pushed again 
7 => return the list of json list of chart as {x:'header1',y:'header1','type':'bar'}
return the json list output like [{x:'header1',y:'header2'},{x:'header5',y:'header10'},...]
'''
prompt2 = '''
Project Description :
The project is related to invoice and matter data. It should address the following use cases or functionalities
1. Ability to summarize key facts, issues and current status of specific matters
2. Based on current status and complexity of a matter, estimate the potential legal costs and timeline to resolution.
3. Provide a range of expected legal fees for specific matter types
4. Identify potential risks with specific matters
5. Provide document summaries
6. Draft documents based on templates and known facts about the matter
7. Review data produced in discovery and identify relevant information
8. Provide proposed timelines and milestones for a matter
9. Identify any outlier or unusual timekeeper rates charged by a firm across matter types/timekeeper levels
10. Calculate average hourly rate charged by each firm by matter type for time period
11. Breakdown legal spend by matter, by timekeeper, by firm for time period
12. Identify matters/firms that are close to exceeding budget or have exceeded budget
13. Identify firms routinely exceeding the matter budget
14. Analyze legal spend trends
15. Forecast legal spend based on current historical data
16. Provide range of estimated legal spend for a specific matter type based on specific timekeeper rates and billing trends.
17. Evaluate the efficiency and cost-effectiveness of firms in handling specific matters/matter types based on timekeeper rates, staffing and overall spend
18. Compare performance metrics of firms
19. Suggest strategies to optimize legal spend with a firm while maintaining quality and effectiveness.
to do =>
1 -> first Analyse the project description given above and generate the insights that what 2D chart combination can be created which is relavent to the project.
2 -> then using this insights , and reading the xlsx file header and data , generate the list of chart that can u created in the format {x:'header1',y:'header1','type':'bar'}
just retune the list of json as output
return the json list output like [{x:'header1',y:'header2',type:'bar'},{x:'header5',y:'header10',type:'bar'},...]
'''
try:
    startChat(file,prompt2)
except :
    startChat(file,prompt2)