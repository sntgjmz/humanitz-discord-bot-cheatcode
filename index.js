require('dotenv').config();
const { Client, GatewayIntentBits, EmbedBuilder } = require('discord.js');
const { Rcon } = require('rcon-client');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

let rcon = null;
let statusMessage = null;

// Helper function to connect to RCON
async function getRcon() {
    if (rcon && rcon.authenticated) return rcon;
    try {
        rcon = new Rcon({
            host: process.env.RCON_HOST,
            port: parseInt(process.env.RCON_PORT || '9002', 10),
            password: process.env.RCON_PASS || process.env.RCON_PASSWORD
        });
        await rcon.connect();
        return rcon;
    } catch (e) {
        console.error('RCON Connection Error:', e.message);
        rcon = null;
        return null;
    }
}

// Function to update Discord Status Embed
async function updateStatus() {
    const channelId = process.env.STATUS_CHANNEL_ID || process.env.CHANNEL_ID;
    if (!channelId) {
        console.error('STATUS_CHANNEL_ID is not defined in environment variables.');
        return;
    }

    const channel = await client.channels.fetch(channelId).catch(() => null);
    if (!channel) {
        console.error(`Could not find channel with ID: ${channelId}`);
        return;
    }

    const conn = await getRcon();
    let isOnline = false;
    let rawResponse = '';

    if (conn) {
        try {
            rawResponse = await conn.send('Players');
            if (rawResponse !== null && rawResponse !== undefined) {
                isOnline = true;
            }
        } catch (err) {
            console.error('Error querying RCON status:', err.message);
            isOnline = false;
        }
    }

    const host = process.env.RCON_HOST || '209.102.250.165';
    const port = process.env.RCON_PORT || '9002';

    const embed = new EmbedBuilder()
        .setTitle('UBELLION SERVER STATUS')
        .setColor(isOnline ? '#00FF00' : '#FF0000')
        .addFields(
            { 
                name: '🌐 Server Status', 
                value: isOnline ? '```ansi\n\u001b[1;32mONLINE\u001b[0m\n```' : '```ansi\n\u001b[1;31mOFFLINE\u001b[0m\n```', 
                inline: true 
            },
            { 
                name: '📌 IP & Port', 
                value: `\`\`\`${host}:${port}\`\`\``, 
                inline: true 
            },
            { 
                name: '📊 Details', 
                value: `\`\`\`\n${isOnline ? (rawResponse.trim() || 'Server active (No players online)') : 'Unable to connect to RCON server.'}\n\`\`\``, 
                inline: false 
            }
        )
        .setFooter({ text: 'HumanitZ Server Watchdog • Auto-updates every 30s' })
        .setTimestamp();

    try {
        if (!statusMessage) {
            // Find existing bot status message to edit instead of creating duplicates
            const messages = await channel.messages.fetch({ limit: 10 }).catch(() => null);
            if (messages) {
                statusMessage = messages.find(m => m.author.id === client.user.id && m.embeds.length > 0);
            }
        }

        if (statusMessage) {
            await statusMessage.edit({ embeds: [embed] });
        } else {
            statusMessage = await channel.send({ embeds: [embed] });
        }
    } catch (err) {
        console.error('Failed to post or edit status message:', err.message);
    }
}

client.once('ready', () => {
    console.log(`Bot online as ${client.user.tag}`);
    updateStatus();
    setInterval(updateStatus, 30000); // 30-second loop
});

// Broadcast in-game message via !say command
client.on('messageCreate', async (msg) => {
    const channelId = process.env.STATUS_CHANNEL_ID || process.env.CHANNEL_ID;
    if (msg.author.bot || msg.channel.id !== channelId) return;

    if (msg.content.startsWith('!say ')) {
        const conn = await getRcon();
        if (!conn) return msg.reply('Cannot connect to RCON server.');
        
        const text = msg.content.slice(5);
        try {
            await conn.send(`announce ${text}`);
            await msg.react('✅');
        } catch (err) {
            console.error('Failed to send RCON command:', err.message);
            await msg.reply('Error sending command to RCON.');
        }
    }
});

client.login(process.env.DISCORD_TOKEN);