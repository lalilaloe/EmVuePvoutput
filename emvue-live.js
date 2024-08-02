const { exec } = require('child_process');
require('dotenv').config();

// Load environment variables
const PVOUTPUT_API_KEY = process.env.PVOUTPUT_API_KEY;
const PVOUTPUT_SYSTEM_ID = process.env.PVOUTPUT_SYSTEM_ID;
const API_URL = 'https://pvoutput.org/service/r2/addstatus.jsp';

// Function to upload data to PVOutput
async function uploadToPVOutput(data) {
    const now = new Date().toLocaleString('nl-NL', { timeZone: 'Europe/Amsterdam' });
    const [datePart, timePart] = now.split(' ');
    const date = datePart.split('-').reverse().join(''); // yyyymmdd format
    const time = timePart.slice(0, 5); // hh:mm format

    //console.log(data)
    const currentUsage = data.find(d => d.channel_num === "1,2,3");
    const solarGeneration = data.find(d => Number(d.channel_num) === 8);

    const channelsFirstSet = [1,2,3]; // Combine channels to provide extended data, modify to your specific groups
    const firstSet = data.filter(c => channelsFirstSet.includes(Number(c.channel_num)));
    const firstSetUsage = firstSet.reduce((total, channel) => total + channel.average_power_watts_5min, 0);
    const channelsSeccondSet = [4,5,6,7];
    const seccondSet = data.filter(c => channelsSeccondSet.includes(Number(c.channel_num)));
    const seccondSetUsage = seccondSet.reduce((total, channel) => total + channel.average_power_watts_5min, 0);

    const generation =  Math.abs((solarGeneration.cumulative_usage_today_kwh * 1000)).toFixed(2); // Convert to Wh
    const consumption = (currentUsage.cumulative_usage_today_kwh * 1000).toFixed(2);
    const powerConsumed = (currentUsage.average_power_watts_5min).toFixed(0);

    const usageFirstSet = (firstSetUsage).toFixed(2);
    const usageSeccondSet = (seccondSetUsage).toFixed(2);

    const params = new URLSearchParams({
        d: date,
        t: time,
        v1: generation,
        v3: consumption,
        v4: powerConsumed,
        v10: usageFirstSet,
        v11: usageSeccondSet
    });

    try {
        // console.log(params)
        const response = await fetch(`${API_URL}?${params}`, {
            method: 'POST',
            headers: {
                'X-Pvoutput-Apikey': PVOUTPUT_API_KEY,
                'X-Pvoutput-SystemId': PVOUTPUT_SYSTEM_ID,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        if (!response.ok) {
            console.error(`Failed to upload data: ${response.statusText}`);
        } else {
            console.log(`Data uploaded successfully for date ${date} time ${time}`);
        }
    } catch (error) {
        console.error(`Error uploading data to PVOutput: ${error.message}`);
    }
}

// Function to fetch data from the Python script
function fetchData() {
    exec('python3 fetch-get.py', (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Python script: ${error.message}`);
            return;
        }
        if (stderr) {
            console.error(`Python script stderr: ${stderr}`);
            return;
        }

        try {
            const usageData = JSON.parse(stdout);
            uploadToPVOutput(usageData);
        } catch (parseError) {
            console.error(`Error parsing JSON output from Python script: ${parseError.message}`);
        }
    });
}

fetchData();
