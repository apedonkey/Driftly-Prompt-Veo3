# Contributing to Driftly YouTube

First off, thank you for considering contributing to Driftly YouTube! 🎉

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When reporting a bug, include:**
- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, etc.)

### 💡 Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:
- A clear and descriptive title
- Detailed description of the proposed feature
- Why this enhancement would be useful
- Possible implementation approach

### 🔧 Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/Driftly-Youtube.git
   cd Driftly-Youtube
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file with your API keys (see `.env.example`)

5. Run the app:
   ```bash
   python app.py
   ```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions small and focused

## Testing

Before submitting a PR:
- Test your changes thoroughly
- Ensure no API keys or credentials are exposed
- Verify the UI works correctly
- Check that video generation still functions

## Questions?

Feel free to open an issue for any questions about contributing!