#!/bin/bash
## expects two commands. The project folder name and the target org.
## Target org can be ommited, though

## get all flow xml files from the project folder
if [ -z "$1" ]; then
    echo "Please provide a project folder"
else
    echo "Starting Flow Metadata Retrieval"
    cd ~/Documents/VSCode/$1
    if [ -z "$2" ]; then
        sf project retrieve start --metadata Flow
    else
        sf project retrieve start --metadata Flow --target-org $2
    fi

    ## create the descriptions for each flow
    echo "Converting Metadata To Markdown Files"
    cd ~/Documents/Flow\ Explainer/salesforce-flow-docs/
    python3 -m automation_doc_exporter --project-root ~/Documents/VSCode/$1
fi
