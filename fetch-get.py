#!/usr/bin/python3

import json
import datetime
from pyemvue import PyEmVue
from pyemvue.enums import Scale, Unit
import math

vue = PyEmVue()
vue.login(token_storage_file='keys.json')

# Initialize tracking variables for each channel
usage_data_per_channel = {}

# Get the current time and define the start time for the past 5 minutes
end_time = datetime.datetime.utcnow()
start_time = end_time - datetime.timedelta(minutes=5)

# Retrieve devices
devices = vue.get_devices()
device_gids = [device.device_gid for device in devices]
device_info = {device.device_gid: device for device in devices}

# Calculate cumulative usage for the day for each channel
day_start = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

for device in devices:
    device_gid = device.device_gid

    # Retrieve cumulative usage for the day and usage in the last 5 minutes
    for channel in device.channels:
        name = channel.name
        if channel.channel_num == "1,2,3": name = "Net"
        if name != 'Balance':
            # Get cumulative usage
            cumulative_usage_today = 0
            if name != "totalUsage" :
                cumulative_usage = vue.get_chart_usage(
                    channel=channel,
                    start=day_start,
                    end=end_time,
                    scale=Scale.DAY.value,
                    unit=Unit.KWH.value
                )[0]

                cumulative_usage_today = sum(value for value in cumulative_usage if value is not None)

            #print(channel.channel_num,name, cumulative_usage_today)
            # Get average power and usage over the past 5 minutes
            usage = 0
            total_power = 0
            total_usage = 0
            total_data_points = 0

            for minute in range(5):
                time = end_time - datetime.timedelta(minutes=minute)
                device_usage_dict = vue.get_device_list_usage(deviceGids=[device_gid], instant=time, scale=Scale.MINUTE.value, unit=Unit.KWH.value)
                channel_data = device_usage_dict.get(device_gid).channels.get(channel.channel_num)
                if channel_data and channel_data.usage is not None:
                    usage = usage
                    total_usage += channel_data.usage
                    total_power += channel_data.usage * 1000 * 60  # Convert kWh to W (Watt-hour to Watt)
                    total_data_points += 1

            # Calculate average usage and power over the 5 minutes
            average_usage_5min = (total_usage / 5) if total_data_points > 0 else 0
            average_power_5min = (total_power / 5) if total_data_points > 0 else 0

            # Store the data for this channel
            usage_data_per_channel[channel.channel_num] = {
                'device_gid': device_gid,
                'channel_num': channel.channel_num,
                'name': name,
                'power_usage_watts': usage,
                'average_power_watts_5min': average_power_5min,
                'average_usage_kwh_5min': average_usage_5min,
                'cumulative_usage_today_kwh': cumulative_usage_today
            }


excluded_names = {"Zonnepanelen", "Net"}
usage_data_per_channel["totalUsage"] ={
    "name": "totalUsage",
    "channel_num": "totalUsage",
    "average_power_watts_5min": math.fsum(obj['average_power_watts_5min'] for i,obj in usage_data_per_channel.items() if obj['name'] not in excluded_names),
    "cumulative_usage_today_kwh":  math.fsum(obj['cumulative_usage_today_kwh'] for i,obj in usage_data_per_channel.items() if obj['name'] not in excluded_names)
}

# Prepare output in JSON format
output = []
for channel_num, data in usage_data_per_channel.items():
    output.append(data)

print(json.dumps(output))
