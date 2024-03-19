# Simple Selenium Parser for Solscan with Google Sheets Integration

This project is a Selenium-based scraper that collects data from Solscan and saves it to a Google Sheet.

## Prerequisites

- Python 3.11+
- Poetry package manager

## Installation

First, clone the repository to your local machine:

```bash
git clone https://github.com/alexmudrak/solscan-parser.git
cd solscan-parser
```

Install the dependencies using Poetry:

```bash
poetry install
```

## Configuration

Before running the application, you need to enable the Google Sheets API and download the `credentials.json` file:

1. Enable the Google Sheets API by visiting:
   [Enable Google Sheets API](https://console.cloud.google.com/apis/enableflow?apiid=sheets.googleapis.com)

2. Download the `credentials.json` file from:
   [Google API Credentials](https://console.cloud.google.com/apis/credentials)

Place the `credentials.json` file in the root directory of the project.

## Running the Application

To run the application, use the following command:

```bash
poetry run python src/main.py
```

## Usage

The application will navigate to the Solscan website, extract the required data, and then authenticate with Google to access and update the specified Google Sheet with the transaction data.
