# Interface guide

## Start locally

Install Python 3.10 or newer. Download this repository using GitHub's **Code → Download ZIP**, extract it, then open a terminal in the extracted project folder.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, `py` may be used instead of `python` if that is how Python is installed. Open the local URL printed in the terminal, normally `http://localhost:8501`. Keep the terminal running while using the app. Stop with Ctrl+C.

## Quick demo

1. Click **Try fictional example**.
2. Review four factors, twelve scoring rules, and a total weight of 100%.
3. Explore **Overview**, **Rules**, and **JSON preview**.
4. Click **Download validated JSON**.

## Use an edited workbook

1. Download the Excel template from the app.
2. Edit the amber cells and save the workbook as `.xlsx`.
3. Upload it and click **Validate and generate**.
4. Fix any reported errors in Excel, save, and upload again.
5. Review the successful result, then download the JSON.

Changing or removing the uploaded file clears the previous result. The sample button always processes the fictional example, even if another workbook is selected; the result's source label identifies what was processed.

## Processing boundaries

Uploads are limited to 5 MB. Expanded archives must stay within 20 MB and 300 entries. The existing workbook contract supports 1,000 data rows per input table. Both input and output validation must pass before a generated-file download is displayed.

The application processes uploaded files in server memory and does not write them to disk or store them in a database. If deployed on another machine, uploads are transferred to that server. The current repository does not include a public deployment.

## Interview walkthrough

Explain the manual configuration problem, run the fictional example, and show the factor/rule previews. Download the template and change only DSCR weight from 40 to 35. Upload it to demonstrate the weight-total error. Correct LTV from 30 to 35, upload again, and show successful generation and download. Explain that the interface shares the same compiler as the CLI and validates the output against a versioned contract before exposing a download.

## Verification

Streamlit AppTest covers initial, example, uploaded, invalid, changed-file, cleared-file, and recovery states. Service tests verify the actual downloadable JSON, its output validation, and file/archive limits. The full suite runs in GitHub Actions.

The local Streamlit server startup and health endpoint were verified. A full browser visual pass was not completed because the browser executable could not be downloaded in the execution environment.
