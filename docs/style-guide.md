# Clearphone Style Guide

This guide covers terminology and writing standards for all Clearphone documentation, error messages, comments, and commit messages.

## Project Goals

Clearphone creates **low-distraction, privacy-respecting phones**. All writing should reflect these goals without disparaging any company or platform.

## Terminology

### Preferred Terms

| Use | Instead of | Reason |
|-----|------------|--------|
| configured phone | safe phone, clean phone | Neutral, accurate |
| low-distraction phone | minimal phone, dumb phone | Describes the goal |
| privacy-respecting phone | private phone, secure phone | Accurate without overclaiming |
| remove | block, disable, kill | Accurate—we uninstall for user 0 |
| pre-installed apps | bloatware (in user-facing docs) | More neutral for general audience |
| replacement apps | alternative apps | Emphasizes the swap |

### Terms to Avoid

| Avoid | Reason |
|-------|--------|
| de-Google, Google-free | Inaccurate (Google develops Android) and unnecessarily adversarial |
| escaping [company]'s ecosystem | Sounds adversarial toward potential partners |
| bloatware (in formal docs) | Use "pre-installed apps" in user-facing content; "bloatware" is acceptable in technical/developer contexts like device profiles |
| safe, secure (as absolutes) | Overclaims—we improve privacy, we don't guarantee security |

### Acceptable in Context

- **bloatware**: Acceptable in device profiles, CLAUDE.md, and developer documentation where technical accuracy matters
- **Samsung/Google/carrier apps**: Fine to name specific sources factually
- **open-source alternatives**: Accurate description of what we install

## Tone

- **Friendly and matter-of-fact**: Not preachy or evangelical
- **Honest about tradeoffs**: Stock camera has better quality; we say so
- **Respectful of all platforms**: We work with Android, not against it
- **No hype**: Let the tool speak for itself

## Error Messages

Error messages should:
1. Explain what happened
2. Explain how to fix it
3. Avoid blame

```
# Good
Profile not found: samsung-s24.toml
Check that the profile path is correct and the file exists.

# Bad
You specified a wrong profile path!
```

## Audience Awareness

- **README.md**: General audience, avoid jargon
- **CLAUDE.md**: Developers and AI assistants, technical language fine
- **Device profiles**: Technical, "bloatware" is acceptable
- **CLI output**: Brief, friendly, clear

## Examples

### Good

> "Clearphone transforms your Android smartphone into a minimal, low-distraction device."

> "Without F-Droid, building a privacy-respecting phone with open-source apps would require users to compile and verify every app themselves."

> "Thank you to Google for keeping Android open enough for projects like this to exist."

### Avoid

> "Clearphone de-Googles your phone and frees you from Big Tech surveillance."

> "Escape Google's ecosystem with our privacy tool."

> "Finally, a way to get rid of all that Google garbage."
