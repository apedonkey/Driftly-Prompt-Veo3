#!/usr/bin/env python3
"""
Configuration validator to ensure all required environment variables are set
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ConfigValidator:
    """Validate configuration and environment variables"""
    
    REQUIRED_ENV_VARS = {
        # Core functionality
        'GROK_API_KEY': {
            'description': 'Grok API key for AI script generation',
            'example': 'xai-your-api-key-here',
            'validate': lambda x: x and x.startswith('xai-') and len(x) > 20
        },
        'FAL_KEY': {
            'description': 'FAL API key for video generation',
            'example': 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xxxxxxxx...',
            'validate': lambda x: x and ':' in x and len(x) > 50
        },
        
        # Google Sheets (optional but recommended)
        'SPREADSHEET_ID': {
            'description': 'Google Sheets ID for topic tracking',
            'example': '1hADNv4Pd_Ikr2SUy8eg_GpcX1cMi_YjIdpAJzLIpeGQ',
            'validate': lambda x: x and len(x) > 20,
            'optional': True
        },
        
        # File paths
        'GOOGLE_SHEETS_CREDENTIALS_PATH': {
            'description': 'Path to Google service account JSON',
            'example': 'config/google_credentials.json',
            'validate': lambda x: x and (not x or Path(x).exists()),
            'optional': True
        },
        'YOUTUBE_CLIENT_SECRETS_PATH': {
            'description': 'Path to YouTube OAuth client secrets',
            'example': 'config/youtube_client_secrets.json',
            'validate': lambda x: x and (not x or Path(x).exists()),
            'optional': True
        },
    }
    
    @staticmethod
    def validate():
        """Validate all configuration"""
        errors = []
        warnings = []
        
        print("🔍 Validating configuration...")
        print("-" * 50)
        
        # Check .env file exists
        if not Path('.env').exists():
            print("⚠️  No .env file found! Creating from template...")
            if Path('.env.example').exists():
                import shutil
                shutil.copy('.env.example', '.env')
                print("✅ Created .env from .env.example")
                print("📝 Please edit .env and add your API keys")
                return False
            else:
                errors.append("No .env or .env.example file found")
        
        # Validate each required variable
        for var_name, config in ConfigValidator.REQUIRED_ENV_VARS.items():
            value = os.environ.get(var_name, '').strip()
            
            if not value:
                if config.get('optional'):
                    warnings.append(f"{var_name}: Not set (optional)")
                else:
                    errors.append(f"{var_name}: Not set (required)")
                continue
            
            # Run validation function if provided
            if 'validate' in config:
                try:
                    if not config['validate'](value):
                        errors.append(f"{var_name}: Invalid format")
                    else:
                        # Mask the value for display
                        masked = value[:10] + '***' if len(value) > 10 else '***'
                        print(f"✅ {var_name}: {masked}")
                except Exception as e:
                    errors.append(f"{var_name}: Validation error - {str(e)}")
        
        # Check for hardcoded secrets in code
        if Path('app.py').exists():
            with open('app.py', 'r') as f:
                content = f.read()
                if 'your-secret-key-here' in content:
                    warnings.append("Flask SECRET_KEY still using default value")
        
        # Display results
        print("-" * 50)
        
        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        
        if errors:
            print("\n❌ Errors:")
            for error in errors:
                print(f"  - {error}")
            print("\n📚 Configuration Guide:")
            print("1. Copy .env.example to .env")
            print("2. Add your API keys to .env")
            print("3. See README.md for detailed setup instructions")
            return False
        
        print("\n✅ Configuration valid!")
        return True
    
    @staticmethod
    def show_example():
        """Show example configuration"""
        print("\n📝 Example .env file:")
        print("-" * 50)
        for var_name, config in ConfigValidator.REQUIRED_ENV_VARS.items():
            optional = " (optional)" if config.get('optional') else ""
            print(f"# {config['description']}{optional}")
            print(f"{var_name}={config['example']}")
            print()

def main():
    """Main validation function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--example':
        ConfigValidator.show_example()
        return 0
    
    if ConfigValidator.validate():
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())