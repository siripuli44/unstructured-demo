from flask import Flask, render_template, request
import os
import json
import networkx as nx
import matplotlib.pyplot as plt
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD
from urllib.parse import quote
import openai

#*********************************Flask set up **************************************************
# Initialize Flask app
app = Flask(__name__)

#********************** AZURE OPEN AI Integration *************************************
# Set the base Azure OpenAI endpoint and your API key
openai.api_type = "azure"
openai.api_base = "<YOUR_OPENAI_ENDPOINT_URL>"
openai.api_version = "2023-05-15"
openai.api_key = "<YOUR_OPENAI_API_KEY>"  # Use environment variable

# Create an RDF graph
g = rdflib.Graph()
EX = Namespace("http://example.org/")
g.bind('ex', EX)

# Function to interact with LLM to process user queries using ChatCompletion
def ask_llm(question):
    response = openai.ChatCompletion.create(
        engine="cfsa-poc-eastus",
        messages=[
            {"role": "system", "content": "You are an expert in generating SPARQL queries. Make sure the output SPARQL query includes valid namespace prefix 'ex' mapped to 'http://example.org/'. Use 'ex:hasSubject', 'ex:hasCategory', and 'ex:sentOn' in the query. Output only the SPARQL query without any explanation or additional text. Do not include any backticks or code block markers."},
            {"role": "user", "content": f"Convert this question into a SPARQL query: {question}. Make sure to use the namespace 'http://example.org/' as 'ex:'."}
        ],
        max_tokens=200,
        temperature=0,
    )
    
    # Get the response content and strip any leading/trailing whitespaces
    sparql_response = response['choices'][0]['message']['content'].strip()
   
    print(f"Generated SPARQL Query: {sparql_response}") 
    return sparql_response


# Function to query the knowledge graph using a SPARQL query from LLM
def query_knowledge_graph_with_llm(sparql_query):
    # Execute the query
    results_list = []
    try:
        g = Graph()
        g.parse("emails_knowledge_graph.ttl", format="ttl") 
        results = g.query(sparql_query)
        print(results)
        # Convert the results to a list
        results_list = list(results)
        
        # Check if any tuples exist
        if len(results_list) > 0:
            print(f"Found {len(results_list)} tuples:")
            for row in results_list:
                print(f"Row: {row}")
        else:
            print("No tuples found.")
    except Exception as e:
        print(f"An error occurred while querying the knowledge graph: {e}")

    #print(results_list)
    return results_list

#==============INSERT FLASK CODE HERE - START========================================================
# Route to handle questions
@app.route('/ask', methods=['POST'])
def ask():
    user_question = request.form['question']
    sparql_query = ask_llm(user_question)
    results = query_knowledge_graph_with_llm(sparql_query)  # Modify this function to return results
    return render_template('results.html', question=user_question, results=results)

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)

# Function to take a user question and run the LLM-generated SPARQL query
def process_query_with_llm(user_question):
    sparql_query = ask_llm(user_question)
    print(f"Generated SPARQL query:\n{sparql_query}")
    query_knowledge_graph_with_llm(sparql_query)

# Example usage
user_question = "List out the community updates sent by the Mayor with date and subject?"
process_query_with_llm(user_question)
#==============INSERT FLASH CODE HERE - END=========================================================


#*************************** Categorize emails and add to Graph***********************************

# Define the folder path where the JSON files are stored
folder_path = '/Projects/AI/unstructured_demo/output'  

# Define more complex categories with keywords for subjects and other metadata
categories = {
    'Community Update': ['recap', 'community', 'summary', 'update', 'newsletter', '202creates'],
    'Official Notice': ['official', 'notice', 'announcement', 'policy', 'legal'],
    'Event Invitation': ['event', 'invitation', 'meeting', 'conference', 'festival'],
    'Internal Communication': ['internal', 'staff', 'team', 'discussion', 'briefing'],
    'Urgent': ['urgent', 'asap', 'immediate', 'important', 'priority'],
    'General': []  # Catch-all category for uncategorized emails
}

def categorize_email(email):
    subject = email['metadata'].get('subject', '').lower()
    sender = email['metadata'].get('sent_from', [''])[0].lower()
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in subject:
                return category
    if "dc.gov" in sender:
        return 'Official Notice'
    return 'General'

def load_json_files_from_folder(folder_path):
    json_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                json_data.extend(data)
    return json_data

# Load the JSON files from the specified folder
emails = load_json_files_from_folder(folder_path)

def add_email_to_knowledge_graph(email_data):
    subject = email_data['metadata'].get('subject', 'Unknown Subject')
    date = email_data['metadata'].get('last_modified', 'Unknown Date')
    sender = email_data['metadata'].get('sent_from', ['Unknown Sender'])[0]
    category = email_data.get('category', 'Uncategorized')
    body = email_data.get('text')

    email_node = URIRef(f"http://example.org/email/{email_data['element_id']}")
    sender_safe = quote(sender)
    sender_node = URIRef(f"http://example.org/person/{sender_safe.replace(' ', '_')}")
    category_node = URIRef(f"http://example.org/category/{category.replace(' ', '_')}")
    date_literal = Literal(date, datatype=XSD.date)
    subject_literal = Literal(subject, datatype=XSD.string)
    category_literal = Literal(category, datatype=XSD.string)
    email_body =  Literal(body, datatype=XSD.string)

    g.add((email_node, RDF.type, EX.Email))
    g.add((email_node, EX.hasSubject, subject_literal))
    g.add((email_node, EX.sentOn, date_literal))
    g.add((email_node, EX.sentBy, sender_node))
    g.add((email_node, EX.hasCategory, category_literal))
    #g.add((email_node, EX.hasBody, email_body))


# Loop through the emails, categorize them, and add to the knowledge graph
for email in emails:
    email['category'] = categorize_email(email)
    add_email_to_knowledge_graph(email)


# *************************Print Graph contents and draw a graph******************************
# Serialize and save the graph (optional)
g.serialize("emails_knowledge_graph.ttl", format="turtle")

# Print out the contents of the graph and 
print("Graph Contents:")
for subj, pred, obj in g:
    print(f"Subject: {subj}, Predicate: {pred}, Object: {obj}")

# Querying the knowledge graph using SPARQL
def query_knowledge_graph():
    query = """

    PREFIX ex: <http://example.org>

    SELECT ?email ?subject ?date ?category
    WHERE {
        ?email ex:hasSubject ?subject .
        ?email ex:sentOn ?date .
        ?email ex:hasCategory ?category .
        FILTER regex(?category, "Community Update")
    }
    """
    results = g.query(query)
    for row in results:
        print(f"Email: {row.email}, Subject: {row.subject}, Date: {row.date}, Sender: {row.sender}, Category: {row.category}")

# Run the query
query_knowledge_graph()

# Load the Turtle file
g = rdflib.Graph()
g.parse("emails_knowledge_graph.ttl", format="turtle")

# Create a NetworkX graph from RDF
nx_graph = nx.DiGraph()
for s, p, o in g:
    nx_graph.add_edge(str(s), str(o))

# Draw the graph
plt.figure(figsize=(12, 12))
nx.draw(nx_graph, with_labels=True, node_size=2000, node_color='skyblue', font_size=10, font_color='black', font_weight='bold')
plt.show()