from rdflib import Graph

# Load the Turtle file
g = Graph()
g.parse("emails_knowledge_graph.ttl", format="ttl")  #Turtle file

# Define your SPARQL query
query = """
SELECT ?email ?date
WHERE {
    ?email a <http://example.org/Email> .
    ?email <http://example.org/sentOn> ?date .
}
"""


query1 = """
PREFIX ex: <http://example.org/>
SELECT ?subject ?category ?date
WHERE {
  ?email ex:hasSubject ?subject ;
         ex:hasCategory ?category ;
         ex:sentOn ?date .
}
"""

query2 = """
SELECT ?subject
WHERE {
?email <http://example.org/hasSubject> ?subject .
}
"""

query3 = """
SELECT ?emailDate
WHERE {
?email <http://example.org/sentOn> ?emailDate.
}
"""

query4 = """
PREFIX ex: <http://example.org/>

SELECT ?subject
WHERE {
  ?email ex:hasSubject ?subject .
}
"""

# Execute the query
results = g.query(query1)

#print(results)

# Print the results
for row in results:
    print(f"Date: {row.date}, Subject: {row.subject}, Category: {row.category}")
    #print(f"Subject: {row.subject}")
