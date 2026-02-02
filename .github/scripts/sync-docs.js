#!/usr/bin/env node
/**
 * Sync README.md with CLI commands.
 *
 * Parses the moltpulse CLI help output and updates the commands table
 * in README.md between the COMMANDS markers.
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const README_FILE = "README.md";

/**
 * Get commands from moltpulse --help
 */
function getCommands() {
  try {
    // Try to get help output from moltpulse
    const helpOutput = execSync("moltpulse --help 2>&1", {
      encoding: "utf8",
      timeout: 10000,
    });

    // Parse commands from the subparser section
    // Looking for lines like: "    run                 Generate a report"
    const commands = [];
    const lines = helpOutput.split("\n");

    let inPositionalArgs = false;
    for (const line of lines) {
      // Detect positional arguments section (contains subcommand list)
      if (line.includes("positional arguments:")) {
        inPositionalArgs = true;
        continue;
      }

      // Stop at options section
      if (inPositionalArgs && line.match(/^options:/i)) {
        break;
      }

      // Parse command lines (indented, with description)
      // Format: "    command              Description here"
      if (inPositionalArgs) {
        const match = line.match(/^\s{4}(\w+)\s{2,}(.+)$/);
        if (match) {
          commands.push({
            name: match[1],
            description: match[2].trim(),
          });
        }
      }
    }

    return commands;
  } catch (error) {
    console.log("Could not run moltpulse --help, using defaults");
    // Return default commands if moltpulse is not available
    return [
      { name: "run", description: "Generate intelligence reports" },
      { name: "config", description: "Manage API keys and settings" },
      { name: "cron", description: "Install scheduled jobs to OpenClaw" },
      { name: "domain", description: "Manage domain configurations" },
      { name: "profile", description: "Manage user profiles" },
    ];
  }
}

/**
 * Generate the commands table for README
 */
function generateCommandsTable(commands) {
  const header = "| Command | Description |\n|---------|-------------|";
  const rows = commands.map((cmd) => {
    return `| \`${cmd.name}\` | ${cmd.description} |`;
  });

  return [header, ...rows].join("\n");
}

/**
 * Update README.md with new commands table
 */
function updateReadme(commands) {
  if (!fs.existsSync(README_FILE)) {
    console.log("README.md not found");
    return false;
  }

  const content = fs.readFileSync(README_FILE, "utf8");

  // Match content between command markers
  const tableRegex =
    /(<!-- COMMANDS:START -->\n)[\s\S]*?(\n<!-- COMMANDS:END -->)/;
  const newTable = generateCommandsTable(commands);

  if (!tableRegex.test(content)) {
    console.log("WARNING: Could not find COMMANDS markers in README.md");
    return false;
  }

  const newContent = content.replace(tableRegex, `$1${newTable}$2`);

  if (newContent === content) {
    return false;
  }

  fs.writeFileSync(README_FILE, newContent);
  return true;
}

function main() {
  console.log("Syncing README.md with CLI commands...");

  const commands = getCommands();
  console.log(`Found ${commands.length} commands`);

  const readmeUpdated = updateReadme(commands);

  if (!readmeUpdated) {
    console.log("README.md is already in sync");
    return;
  }

  console.log("Updated README.md commands table");
}

main();
