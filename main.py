#import libraries
#import streamlit
from re import X
import streamlit as st
#specklepy libraries
from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
#import pandas
import pandas as pd
#plotly express. fast and easy way to generate graphs.
import plotly.express as px

#page config
st.set_page_config(
    page_title="Speckle Stream Activity",
    page_icon="📊"
)
#header container
header = st.container()
#header
with header:
    st.title("Speckle Stream Activity App📈")

with st.expander("About this app📣", expanded=True):

    st.markdown(
        """This is a beginner web app developed using Streamlit. My goal was to understand how to interact with Speckle API using SpecklePy, 
        analyze what is received and its structure. This was easy and fun experiment.
        """
    )

#--------------------
#input and report containers
input = st.container()
viewer = st.container()
report = st.container()
graphs = st.container()

#--------------------

#lets get inputs
with input:
    st.subheader("Inputs...")
    #3 columns for 3 inputs
    serverCol, tokenCol = st.columns([1,3])
    #input variables
    speckleServer = serverCol.text_input("Server URL", "speckle.xyz", help="Speckle server to connect.")
    speckleToken = tokenCol.text_input("Speckle token", "087fea753d12f91a6f692c8ea087c1bf4112e93ed7", help="If you don't know how to get your token, take a look at this [link](https://speckle.guide/dev/tokens.html)👈")

    #--------------
    #Speckle Client
    client = SpeckleClient(host=speckleServer)
    #get account from token
    account = get_account_from_token(speckleToken, speckleServer)
    #authenticate using the account
    client.authenticate_with_account(account)
    #--------------------------------

    #get list of streams
    streams = client.stream.list()
    #get stream names
    streamNames = [s.name for s in streams]
    #create dropdown for user to select stream name
    sName = st.selectbox(label="Select your stream", options=streamNames, help="Select your stream from the dropdown")
    #get stream from name
    stream = client.stream.search(sName)[0]
    #st.write(stream)
    #list commits
    scommits = client.commit.list(stream.id,limit=100)
    #list branches
    branches = client.branch.list(stream.id)
    #-------------

#create a definition to convert your list to markdown
def listToMarkdown(list, column):
    list = ["- " + i + " \n" for i in list]
    list = "".join(list)
    return column.markdown(list)

#create a definition that creates iframe from commit id
def commit2viewer(stream, commit, height=400) -> str:
    embed_src = "https://speckle.xyz/embed?stream="+stream.id+"&commit="+commit.id
    return st.components.v1.iframe(src=embed_src, height=height)

#Speckle Viewer
with viewer:
    st.subheader("Latest Commit👇")
    commit2viewer(stream, scommits[0])

#OUTPUTs
with report:
    st.subheader("Statistics")
    
    #4 columns for 4 Cards
    branchCol, commitCol, connectorCol, contributorCol = st.columns(4)
    #-----------------
    #Branch Column
    branchCol.metric(label = "Number of branches", value= len(branches))
    #branch names as markdown list
    branchNames = [b.name for b in branches]
    listToMarkdown(branchNames, branchCol)

    #Commit Column
    commitCol.metric(label = "Number of commits", value= len(scommits))

    #Connector Column
    #connector list
    connectorList = [c.sourceApplication for c in scommits]
    #number of connectors
    connectorCol.metric(label="Number of connectors", value= len(dict.fromkeys([c.sourceApplication for c in scommits])))
    #get connector names
    connectorNames = list(dict.fromkeys(connectorList))
    #convert it to markdown list
    listToMarkdown(connectorNames, connectorCol)

    #Contributor Column
    #unique contributor names
    contributorNames = list(dict.fromkeys([col.name for col in stream.collaborators]))
    #number of contributors
    contributorCol.metric(label = "Number of collaborators", value= len(contributorNames))

    #convert it to markdown list
    listToMarkdown(contributorNames,contributorCol)    

with graphs:
    st.subheader("Graphs")
    branch_graph_col, connector_graph_col, collaborator_graph_col = st.columns([2,1,1])
    #-------------------------
    #CONNECTOR CHART
    #commits to dataframe
    scommits = pd.DataFrame.from_dict([c.dict() for c in scommits])
    #get apps from commits
    apps = scommits["sourceApplication"]
    #reset index
    apps = apps.value_counts().reset_index()
    #rename columns
    apps.columns=["app","count"]
    #donut chart
    fig = px.pie(apps, names=apps["app"],values=apps["count"], hole=0.5)
    #set dimensions of the chart
    fig.update_layout(
        showlegend=False,
        margin=dict(l=2, r=2, t=2, b=2),
        height=200,
        yaxis_scaleanchor="x"
        )
    #set width of the chart so it uses column width
    connector_graph_col.plotly_chart(fig, use_container_width=True)
    #-------------------------
    #-------------------------
    #COLLABORATOR CHART
    #get authors from commits
    authors = scommits["authorName"].value_counts().reset_index()
    #rename columns
    authors.columns=["author","count"]
    #create our chart
    authorFig = px.pie(authors, names=authors["author"], values=authors["count"],hole=0.5)
    authorFig.update_layout(
        showlegend=False,
        margin=dict(l=1,r=1,t=1,b=1),
        height=200,
        yaxis_scaleanchor="x",)
    collaborator_graph_col.plotly_chart(authorFig, use_container_width=True)
    #-------------------------

    #BRANCH ACTIVITY
    #-------------------------
    branch_counts = pd.DataFrame([[branch.name, branch.commits.totalCount] for branch in branches])
    branch_counts.columns = ["branchName", "totalCommits"]
    branch_count_graph = px.bar(branch_counts, x=branch_counts.branchName, y=branch_counts.totalCommits, color=branch_counts.branchName, labels={"branchName":"","totalCommits":""})
    branch_count_graph.update_layout(
        showlegend = False,
        margin = dict(l=1,r=1,t=1,b=1),
        height=220
    )
    branch_graph_col.plotly_chart(branch_count_graph, use_container_width=True)
    #-------------------------

    #-------------------------
    #COMMIT PANDAS TABLE
    st.subheader("Commit Activity Timeline 🕒")
    #created at parameter to dataframe with counts
    cdate = pd.to_datetime(scommits["createdAt"]).dt.date.value_counts().reset_index().sort_values("index")
    #date range to fill null dates.
    null_days = pd.date_range(start=cdate["index"].min(), end=cdate["index"].max())
    #add null days to table
    cdate = cdate.set_index("index").reindex(null_days, fill_value=0)
    #reset index
    cdate = cdate.reset_index()
    #rename columns
    cdate.columns = ["date", "count"]
    #redate indexed dates
    cdate["date"] = pd.to_datetime(cdate["date"]).dt.date
    #------------------------

    #------------------------
    #COMMIT ACTIVITY LINE CHART
    #line chart
    fig = px.line(cdate, x=cdate["date"], y=cdate["count"], markers =True)
    #recolor line
    
    #Show Chart
    st.plotly_chart(fig, use_container_width=True)
    #------------------------

