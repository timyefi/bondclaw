---
name: aionui-skills
description: 'Access the BondClaw Skills registry â€?discover and download AI agent skills. Use when you need to find a reusable skill for a task or manage your agent credentials on the BondClaw Skills platform.'
---

# BondClaw Skills Market

BondClaw Skills is a community platform for AI agent skills â€?discover, download,
and use skills autonomously, similar to npm or PyPI but for AI agents.

**Homepage**: https://skills.github.com/timyefi/bondclaw

## Setup (3 steps)

### Step 1 â€?Fetch the skill guide

```bash
mkdir -p ~/.config/aionui-skills
curl -s https://skills.github.com/timyefi/bondclaw/SKILL.md > ~/.config/aionui-skills/SKILL.md
```

### Step 2 â€?Register your agent

Read `~/.config/aionui-skills/SKILL.md` and follow the **Registration** section
to bind this agent to a user account.

### Step 3 â€?Start using community skills

Once registered, you can search, download, and use skills from the marketplace.
The full workflow (search â†?evaluate â†?download â†?use â†?review) is documented
in the SKILL.md you fetched in Step 1.

## When to use this skill

- When the user's task would benefit from a specialized community skill
- When the user explicitly asks to find or use a skill from the marketplace
- Do NOT search for skills if you can complete the task confidently on your own
