#!/bin/bash
## expects two commands. The project folder name and the target org.
## Target org can be ommited, though

## set your directories
d_project="$HOME/Documents/VSCode"
d_autodocex="$HOME/Documents/Flow Explainer/salesforce-flow-docs/"

## get all flow xml files from the project folder
if [ -z "$1" ]; then
    echo "Please provide a project folder"
else
    echo "Starting Flow Metadata Retrieval"
    cd "$d_project"/$1
    if [ -z "$2" ]; then
        sf project retrieve start --metadata Flow
    else
        sf project retrieve start --metadata Flow --target-org $2
    fi

    ## create the descriptions for each flow
    echo "Converting Metadata To Markdown Files"
    cd "$d_autodocex"
    python3 -m automation_doc_exporter --project-root "$d_project"/$1
fi
