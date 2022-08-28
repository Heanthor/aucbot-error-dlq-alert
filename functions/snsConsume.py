import sys
sys.path.insert(0, 'functions/vendor')

import discord
from discord.ext import tasks
import json
import asyncio

import os

CONSOLE_URL = "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:alarm/%s?"
"""
Sample "Message" key:
{
  "AlarmName": "aucbot-pricealert-undelivered-messages",
  "AlarmDescription": null,
  "AWSAccountId": "533639758947",
  "AlarmConfigurationUpdatedTimestamp": "2022-08-28T15:38:30.249+0000",
  "NewStateValue": "ALARM",
  "NewStateReason": "Threshold Crossed: 1 out of the last 1 datapoints [0.0 (28/08/22 15:34:00)] was greater than or equal to the threshold (0.0) (minimum 1 datapoint for OK -> ALARM transition).",
  "StateChangeTime": "2022-08-28T15:39:16.518+0000",
  "Region": "US East (N. Virginia)",
  "AlarmArn": "arn:aws:cloudwatch:us-east-1:533639758947:alarm:aucbot-pricealert-undelivered-messages",
  "OldStateValue": "OK",
  "OKActions": [],
  "AlarmActions": ["arn:aws:sns:us-east-1:533639758947:aucbot-prod-dlq-2"],
  "InsufficientDataActions": [],
  "Trigger": {
    "MetricName": "ApproximateNumberOfMessagesNotVisible",
    "Namespace": "AWS/SQS",
    "StatisticType": "Statistic",
    "Statistic": "AVERAGE",
    "Unit": null,
    "Dimensions": [{ "value": "ADSScan.fifo", "name": "QueueName" }],
    "Period": 300,
    "EvaluationPeriods": 1,
    "DatapointsToAlarm": 1,
    "ComparisonOperator": "GreaterThanOrEqualToThreshold",
    "Threshold": 0.0,
    "TreatMissingData": "missing",
    "EvaluateLowSampleCountPercentile": ""
  }
}
"""

def handler(event, context):
    intents = discord.Intents.default()

    client = DiscordClient(event, intents=intents)
    asyncio.run(client.start(os.getenv("DISCORD_TOKEN")))

    print(event)
    return { 
        'message' : "success"
    }

class DiscordClient(discord.Client):
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.channel_id = int(os.getenv("CHANNEL_ID"))
        self.group_id = int(os.getenv("ROLE_ID"))

    def build_message(self):
        record = self.event["Records"][0]["Sns"]
        message = json.loads(record['Message'])
        msg = f"<@&{self.group_id}> **Aucbot error triggered:**\n"
        msg += f"**Subject:** {record['Subject']}\n"
        msg += f"**Metric:** {message['Trigger']['MetricName']}\n"
        msg += f"**Detail:** ```{message['NewStateReason']}```\n"
        
        msg += f"View alarm: {CONSOLE_URL % message['AlarmName']}"

        return msg

    async def setup_hook(self) -> None:
        self.alert_error.start()

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    @tasks.loop(seconds=10)
    async def alert_error(self):
        await self.wait_until_ready()
        channel = self.get_channel(self.channel_id)
        if not self.is_closed():
            msg = self.build_message()
            print("Sending message: ", msg)
            await channel.send(msg)
            await self.close()
