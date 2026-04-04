---
title: "# Automating Garmin Data Integration with ChatGPT Using Scheduled Data Feeds"
author: "Dr. Hernani Costa"
author_url: "https://drhernanicosta.com"
author_linkedin: "https://www.linkedin.com/in/hernani-costa-ai-ceo-firstaimovers/"
publication: "First AI Movers"
publication_url: "https://firstaimovers.com"
canonical_url: "https://insights.firstaimovers.com/automating-garmin-data-integration-with-chatgpt-using-scheduled-data-feeds-b422add48e56"
published_date: "2025-05-12"
license: "CC BY 4.0"
---
# Automating Garmin Data Integration with ChatGPT Using Scheduled Data Feeds

---

Anyone interested in automating this?

---

This report details methods to automatically integrate Garmin data (e.g. Fenix 6 Pro) into a ChatGPT-based personal coaching assistant using OpenAI's GPT-4o model. We explore both manual and fully automated approaches while addressing security, reliability, and usability considerations.

— -

## Manual Data Transfer Workflow

For users preferring direct control, this method uses Garmin Connect's export functionality with manual ChatGPT interactions:

### Step 1: Daily Data Export from Garmin Connect

1. Navigate to Garmin Connect's **Daily Summary** page.

1. 2. Use browser developer tools to extract JSON data via network requests:

1. . \`\`\`javascript

1. . // Console command to fetch yesterday's data

1. . fetch(`https://connect.garmin.com/modern/proxy/wellness-service/wellness/dailySummaryChart/${username}?date=${getYesterdayDate()}`)

1. . .then(response => response.json())

1. . .then(data => console.log(JSON.stringify(data)));

1. . \`\`\`

1. 3. Copy JSON output containing:

1. . — Hourly heart rate.

1. . — Sleep stages.

1. . — Activity minutes.

1. . — Stress levels\[11]\[16]

### Step 2: ChatGPT Interaction Template

Paste structured prompts into ChatGPT:

```

/coach Today's Health Data:

- Resting HR: 52 bpm ▲2% from baseline

- - Sleep: 6h24m (Deep: 1h12m, REM: 1h48m)

- - Steps: 8,432 (76% of goal)

- - Stress Avg: 42 (Moderate)

- [Paste full JSON here]

- Generate recovery recommendations.

- ```

- This approach maintains user control but requires daily manual effort[12][15].

— -

## Semi-Automated Script-Based Solution

### Architecture Overview

```mermaid

graph TD

. A[Garmin Fenix 6 Pro] — >|Sync| B(Garmin Connect)

. B — > C[Python Script]

. C — >|Store| D[(Local SQLite DB)]

. D — > E[ChatGPT API]

. E — > F[Coaching Insights]

```

### Implementation Code

```

from garminconnect import Garmin

import sqlite3

from openai import OpenAI

import schedule

# Initialize components

garmin_client = Garmin("user@example.com", "password")

openai_client = OpenAI(api_key="sk-...")

db_conn = sqlite3.connect('health_data.db')

def daily_fetch():

. # Get yesterday's data

. data = garmin_client.get_wellness_data(datetime.date.today() — datetime.timedelta(days=1))

.

. # Store locally

. cursor = db_conn.cursor()

. cursor.execute('''

. INSERT INTO daily_metrics

. (date, steps, avg_hr, sleep_duration)

. VALUES (?,?,?,?)

. ''', (data['date'], data['steps'], data['heart_rate'], data['sleep']))

.

. # Generate summary

. response = openai_client.chat.completions.create(

. model="gpt-4o",

. tools=[health_analysis_tool],

. messages=[{"role": "user", "content": f"Analyze: {data}"}]

. )

. print(response.choices[0].message.content)

# Schedule daily 6AM execution.

schedule.every().day.at("06:00").do(daily_fetch)

while True:

. schedule.run_pending()

. time.sleep(60)

```

Key Features:

- Local data storage for privacy[17]

- - Automated morning analysis.

- - Fallback to manual execution if needed[14]

— -

## Full Automation with Serverless Architecture

For hands-free operation using cloud services:

### AWS Lambda Implementation

```

Resources:

. DailyGarminLambda:

. Type: AWS::Serverless::Function

. Properties:

. Runtime: python3.9

. Handler: index.handler

. Policies:

. — SecretsManagerReadWrite

. Environment:

. Variables:

. GARMIN_USER: !Ref GarminUserSecret

. OPENAI_KEY: !Ref OpenAIKeySecret

. CodeUri: ./src/

. Events:

. DailySchedule:

. Type: Schedule

. Properties:

. Schedule: cron(0 12 * * ? *)

```

```

# src/index.py

def handler(event, context):

. client = Garmin(os.environ['GARMIN_USER'], get_secret('GARMIN_PASS'))

. data = client.get_daily_summary()

.

. prompt = f"""

. As a coaching assistant, analyze this daily data:

. {json.dumps(data)}

. Highlight 3 improvement areas and suggest tomorrow's workout.

. """

.

. openai_response = openai.ChatCompletion.create(

. model="gpt-4o",

. messages=[{"role": "user", "content": prompt}]

. )

.

. send_sms(os.environ['USER_PHONE'], openai_response.choices[0].message.content)

```

Advantages:

- Zero manual intervention.

- - SMS/email delivery of insights[17]

- - Automatic credential rotation via AWS Secrets Manager.

— -

## ChatGPT UI Integration Strategies

### Method 1: Custom GPT Configuration

1. Create **Custom GPT** in ChatGPT interface.

1. 2. Upload historical health data CSV for baseline analysis.

1. 3. Configure instructions:

1. . \`\`\`

1. . — Request Garmin data via /garmin\_update command

1. . — Analyze trends against user's 30-day average

1. . — Generate PDF workout plans

1. . \`\`\`

1. 4. Enable **Code Interpreter** for data visualization[15]

### Method 2: Plugin Development

```

// chrome-extension/content-script.js

document.addEventListener('garminData', (e) => {

. const chatInput = document.querySelector('textarea');

. chatInput.value = `/analyze_garmin ${JSON.stringify(e.detail)}`;

. chatInput.dispatchEvent(new Event('input'));

});

```

This browser extension auto-injects Garmin data into ChatGPT's input when users visit Garmin Connect[9].

— -

## Security Considerations

| Aspect. | Implementation. |

| — — — — — — — — — — — | — — — — — — — — — — — — — — — — — — — — -|

| Credential Storage. | AWS Secrets Manager with rotation[17] |.

| Data Transit. | TLS 1.3 encryption. |

| Access Control. | IAM role-based permissions. |

| Audit Logging. | CloudTrail monitoring. |

| Rate Limiting. | 5 requests/minute queue. |

— -

## Recommended Implementation Path

1. **Initial Phase**

1. . — Manual data exports with template prompts.

1. . — Local Python script for daily analysis\[8]\[13]

1. **Intermediate Phase**

. — AWS Lambda scheduled daily fetch.

. — SMS delivery via SNS.

1. **Advanced Phase**

. — Custom GPT with persistent memory.

. — Auto-sync browser extension.

This phased approach balances complexity with immediate usability while building toward full automation\[12]\[14].

— -

## Troubleshooting Common Issues

**Authentication Failures**

- Implement OAuth 2.0 refresh tokens.

- - Use headless browser authentication flow[6]

- \`\`\`python

- from garminconnect import (

- . Garmin,

- . GarminConnectAuthenticationError,

- . GarminConnectConnectionError,

- )

try:

. client = Garmin("user", "pass")

. client.login()

except GarminConnectAuthenticationError:

. # Handle 2FA

. client.login\_2fa()

```

**Data Formatting**

Convert Garmin's nested JSON to flattened CSV:

```python

def flatten_json(data):

. return {

. 'date': data['calendarDate'],

. 'steps': data['steps'],

. 'sleep_score': data['sleep']['sleepScore'],

. 'stress_avg': data['stress']['avgStressLevel']

. }

```

**Model Context Limits**

Implement summarization pipeline:

```

Raw Data → Daily Summary → Weekly Trends → Monthly Report

```

Chunking strategy maintains context while providing granular insights[11].

— -

This integration enables real-time health coaching through automated data synthesis. By combining Garmin's detailed biometrics with GPT-4o's analytical capabilities, users receive personalized guidance while maintaining full control over their data flow.

Sources

[1] How Do I Export Data Out of Garmin Connect? https://support.garmin.com/en-US/?faq=W1TvTPW8JZ6LfJSfK512Q8

[2] garminexport — PyPI https://pypi.org/project/garminexport/

[3] Export Data from connect:Health-Statistics — It looks as if I will have to ... https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/272759/export-data-from-connect-health-statistics---it-looks-as-if-i-will-have-to-write-it-from-the-screen-to-ms-excel-manually--

[4] Garmin Connect Developer Program: An Inside Look at API ... https://www.youtube.com/watch?v=K1GJlvh7-b0

[5] How to Schedule Workouts Using the Calendar in Garmin Connect https://support.garmin.com/en-US/?faq=XRcMvEtKdf7yBf8My9jua6

[6] Garmin Connect activity exporter and backup tool — GitHub https://github.com/petergardfjall/garminexport

[7] Is there a way to export daily activity(steps & sleep)from Garmin ... https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/117369/is-there-a-way-to-export-daily-activity-steps-sleep-from-garmin-connect-to-csv-xls

[8] Python 3 API wrapper for Garmin Connect to get activity statistics https://github.com/cyberjunky/python-garminconnect

[9] Download Daily Steps — Garmin Connect Web — Mobile Apps & Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/155247/download-daily-steps

[10] Exporting all data from garmin connect — Reddit https://www.reddit.com/r/Garmin/comments/aorx8l/exporting_all_data_from_garmin\_connect/

[11] Garmin Daily Summary Export Format https://support.mydatahelps.org/hc/en-us/articles/14852974939667-Garmin-Daily-Summary-Export-Format

[12] How do I get my daily automatic export of runs/activities back? https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/380692/how-do-i-get-my-daily-automatic-export-of-runs-activities-back

[13] python-garminconnect/garminconnect/**init**.py at master — GitHub https://github.com/cyberjunky/python-garminconnect/blob/master/garminconnect/**init**.py

[14] How do I batch export all of my historical data, not just one activity at ... https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/227203/how-do-i-batch-export-all-of-my-historical-data-not-just-one-activity-at-a-time

[15] Exporting history of daily steps — Garmin — Reddit https://www.reddit.com/r/Garmin/comments/1es2py1/exporting_history_of_daily_steps/

[16] How to export all heart rate data : r/Garmin — Reddit https://www.reddit.com/r/Garmin/comments/8rpq9y/how_to_export_all_heart_rate_data/

[17] garmindb — PyPI https://pypi.org/project/garmindb/

[18] How to export all data from Garmin Connect? — Mobile Apps & Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/126453/how-to-export-all-data-from-garmin-connect

[19] Exporting Garmin data to TrainingPeaks taking a very long time https://forums.garmin.com/outdoor-recreation/outdoor-recreation/f/fenix-6-series/285099/exporting-garmin-data-to-trainingpeaks-taking-a-very-long-time---what-s-wrong

[20] Training API | Garmin Connect Developer Program https://developer.garmin.com/gc-developer-program/training-api/

[21] Export all-day RAW heart rate data — Garmin Connect Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/320208/export-all-day-raw-heart-rate-data

[22] garminconnect — PyPI https://pypi.org/project/garminconnect/0.1.53/

[23] How to export full data of my activities from Garmin Connect? — Reddit https://www.reddit.com/r/Garmin/comments/hzbwnl/how_to_export_full_data_of_my_activities_from/

[24] Activity API | Garmin Connect Developer Program https://developer.garmin.com/gc-developer-program/activity-api/

[25] Is there a way to export my list of activities from Garmin Connect ... https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/234309/is-there-a-way-to-export-my-list-of-activities-from-garmin-connect-including-the-activity-id

[26] Personal use of Garmin API — Reddit https://www.reddit.com/r/Garmin/comments/114eh9y/personal_use_of_garmin_api/

[27] Dummy's guide to exporting... to Garmin Connect — Intervals.icu Forum https://forum.intervals.icu/t/dummys-guide-to-exporting-to-garmin-connect/16880

[28] Garmin export — bas' notes https://familiehopman.nl/garminexport/

[29] Payment Required? · Issue #54 · pe-st/garmin-connect-export — GitHub https://github.com/pe-st/garmin-connect-export/issues/54

[30] Fetching and storing activities from Garmin Connect with Strapi and ... https://mxd.codes/articles/fetching-and-storing-activities-from-garmin-connect-with-strapi-and-visualizing-them-with-next-js

[31] How can I manually export my Garmin Connect™ Activities into ... https://help.trainingpeaks.com/hc/en-us/articles/204070844-How-can-I-manually-export-my-Garmin-Connect-Activities-into-TrainingPeaks

[32] Automating export of raw (.FIT?) data from GC — Garmin — Reddit https://www.reddit.com/r/Garmin/comments/1hm0qk7/automating_export_of_raw_fit_data_from\_gc/

[33] Python script for managing and scheduling garmin connect workouts https://www.reddit.com/r/Marathon_Training/comments/1g76ck6/python_script_for_managing_and_scheduling\_garmin/

[34] Terra — Fitness and Health API to connect to your app https://tryterra.co

[35] Garmin Export Overview — MyDataHelps™ Designer Help Center https://support.mydatahelps.org/hc/en-us/articles/14853338739731-Garmin-Export-Overview

[36] pe-st/garmin-connect-export — GitHub https://github.com/pe-st/garmin-connect-export

[37] How to export all data from Garmin Connect? — Mobile Apps & Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/126453/how-to-export-all-data-from-garmin-connect

[38] Garmin data — Day One Forums https://forums.dayoneapp.com/forums/topic/garmin-data/

[39] WHY cant we download a csv file of our data? — Garmin Forums https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-mobile-andriod/192606/why-cant-we-download-a-csv-file-of-our-data

[40] How Do I Export Data Out of Garmin Connect? | Forerunner 955 https://support.garmin.com/en-IN/?faq=W1TvTPW8JZ6LfJSfK512Q8&identifier=777655&tab=topics

[41] Copy Activity from one day to another — Garmin Connect Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/346400/copy-activity-from-one-day-to-another

[42] How Do I Export Data Out of Garmin Connect? | Forerunner® 45 https://support.garmin.com/lv-LV/?productID=641121&faq=W1TvTPW8JZ6LfJSfK512Q8&tab=

[43] How Do I Export Dive Information? | Garmin Customer Support https://support.garmin.com/en-US/?faq=NxZWyZYGqL17VNBMKDUjb5

[44] Activity data download for personal use — Garmin Connect Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/271967/activity-data-download-for-personal-use

[45] Turn Garmin Connect Daily Export Files into an Excel File with Data ... https://www.reddit.com/r/Garmin/comments/64yme9/turn_garmin_connect_daily_export_files_into\_an/

[46] Extract 24/7 heart rate data from Garmin COnnect — Reddit https://www.reddit.com/r/Garmin/comments/h85r02/extract_247_heart_rate_data_from_garmin\_connect/

[47] Analysis of Runing Activities from Garmin Watch Using Python https://towardsdatascience.com/analysis-of-runing-activities-from-garmin-watch-using-python-99609f83314e/

[48] Daily Summary — New Website — Garmin Connect Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/163843/daily-summary---new-website

[49] Daily data from Garmin sports watch | algrt.hm https://algrt.hm/2020-05-04-data-from-garmin/

[50] Export daily steps on Garmin Connect — Reddit https://www.reddit.com/r/Garmin/comments/1cx85hn/export_daily_steps_on_garmin\_connect/

[51] Running on my own — Francesco Schwarz https://isellsoap.net/articles/running-on-my-own/

[52] Cron Job for Data Feed Addon — General Questions — CS-Cart Forums https://forum.cs-cart.com/t/cron-job-for-data-feed-addon/12914

[53] Garmin integration — Terra API https://tryterra.co/integrations/garmin

[54] export health data — Garmin Connect Web — Mobile Apps & Web https://forums.garmin.com/apps-software/mobile-apps-web/f/garmin-connect-web/142198/export-health-data

[55] How to Export All Activities to CSV file? : r/Garmin — Reddit https://www.reddit.com/r/Garmin/comments/133tdqu/how_to_export_all_activities_to_csv\_file/

[56] Video of How I Use Python to Quickly Summarize and Plot Hiking ... https://adventuresinroamance.com/video-of-how-i-use-python-to-quickly-summarize-and-plot-hiking-data-from-garmin/

---

**Author:** [Dr. Hernani Costa](https://drhernanicosta.com) — Founder of [First AI Movers](https://firstaimovers.com) and [Core Ventures](https://coreventures.xyz). AI Architect, Strategic Advisor, and Fractional CTO helping Top Worldwide Innovation Companies navigate AI Innovations. PhD in Computational Linguistics, 25+ years in technology.

*Originally published at [First AI Movers](https://insights.firstaimovers.com/automating-garmin-data-integration-with-chatgpt-using-scheduled-data-feeds-b422add48e56) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).*