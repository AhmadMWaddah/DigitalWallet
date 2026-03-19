#!/bin/bash

# --#-- Phase 7 Manual Testing Script
# This script sets up test data and provides interactive testing options

set -e

echo "=============================================="
echo "  Phase 7: Staff & Analytics Testing Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --#-- Configuration
DJANGO_SETTINGS="core.settings.dev"
MANAGE="python manage.py"

# --#-- Helper Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# --#-- Check Prerequisites
echo "Step 1: Checking Prerequisites..."
echo "----------------------------------------------"

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_error "Virtual environment not activated!"
    echo "Run: source .env_digital_wallet/bin/activate"
    exit 1
else
    print_success "Virtual environment active"
fi

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    print_error "Django not installed!"
    exit 1
else
    print_success "Django installed"
fi

# Check if Redis is running
if redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is running"
else
    print_warning "Redis not running. Starting Redis..."
    redis-server --daemonize yes
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis started successfully"
    else
        print_error "Failed to start Redis"
        exit 1
    fi
fi

echo ""

# --#-- Create Test Data
echo "Step 2: Creating Test Data..."
echo "----------------------------------------------"

$MANAGE shell --settings=$DJANGO_SETTINGS << 'EOF'
from accounts.models import CustomUser, UserType
from wallet.models import Wallet, Transaction
from wallet.services import transfer_funds
from decimal import Decimal
from django.utils import timezone

print("Creating test users...")

# Get or create Staff User
staff, created = CustomUser.objects.get_or_create(
    email="staff@test.com",
    defaults={
        "user_type": UserType.STAFF,
    }
)
if created:
    staff.set_password("testpass123")
    staff.save()
    print("  ✅ Created staff user: staff@test.com / testpass123")
else:
    print("  ℹ️  Staff user already exists")

# Get or create Client User 1 (Old Account)
client1, created = CustomUser.objects.get_or_create(
    email="client1@test.com",
    defaults={
        "user_type": UserType.CLIENT,
    }
)
if created:
    client1.set_password("testpass123")
    client1.save()
    wallet1, _ = Wallet.objects.get_or_create(
        client_profile=client1.client_profile,
        defaults={"balance": Decimal("50000.00")}
    )
    print("  ✅ Created client1: client1@test.com / testpass123 (Balance: $50,000)")
else:
    print("  ℹ️  Client1 already exists")
    wallet1 = client1.client_profile.wallet

# Get or create Client User 2 (New Account - for Rule 3 testing)
client2, created = CustomUser.objects.get_or_create(
    email="newclient@test.com",
    defaults={
        "user_type": UserType.CLIENT,
    }
)
if created:
    client2.set_password("testpass123")
    # Set account as very new (created today)
    client2.date_joined = timezone.now()
    client2.save()
    wallet2, _ = Wallet.objects.get_or_create(
        client_profile=client2.client_profile,
        defaults={"balance": Decimal("5000.00")}
    )
    print("  ✅ Created new client: newclient@test.com / testpass123 (NEW ACCOUNT)")
else:
    print("  ℹ️  New client already exists")
    wallet2 = client2.client_profile.wallet

# Get or create Receiver User
receiver, created = CustomUser.objects.get_or_create(
    email="receiver@test.com",
    defaults={
        "user_type": UserType.CLIENT,
    }
)
if created:
    receiver.set_password("testpass123")
    receiver.save()
    receiver_wallet, _ = Wallet.objects.get_or_create(
        client_profile=receiver.client_profile,
        defaults={"balance": Decimal("1000.00")}
    )
    print("  ✅ Created receiver: receiver@test.com / testpass123")
else:
    print("  ℹ️  Receiver already exists")
    receiver_wallet = receiver.client_profile.wallet

# Create test transactions for analytics
print("\nCreating test transactions for analytics...")

# Check if we already have test transactions
existing_count = Transaction.objects.filter(wallet=wallet1).count()
if existing_count < 5:
    # Create some deposits
    Transaction.objects.get_or_create(
        wallet=wallet1,
        reference_id="TEST-DEP-001",
        defaults={
            "amount": Decimal("5000.00"),
            "type": "DEPOSIT",
            "status": "COMPLETED",
            "created_at": timezone.now() - timezone.timedelta(days=5),
        }
    )
    
    Transaction.objects.get_or_create(
        wallet=wallet1,
        reference_id="TEST-DEP-002",
        defaults={
            "amount": Decimal("3000.00"),
            "type": "DEPOSIT",
            "status": "COMPLETED",
            "created_at": timezone.now() - timezone.timedelta(days=15),
        }
    )
    
    # Create some withdrawals
    Transaction.objects.get_or_create(
        wallet=wallet1,
        reference_id="TEST-WDR-001",
        defaults={
            "amount": Decimal("1000.00"),
            "type": "WITHDRAWAL",
            "status": "COMPLETED",
            "created_at": timezone.now() - timezone.timedelta(days=10),
        }
    )
    
    # Create some transfers
    Transaction.objects.get_or_create(
        wallet=wallet1,
        counterparty_wallet=receiver_wallet,
        reference_id="TEST-TRF-001",
        defaults={
            "amount": Decimal("2000.00"),
            "type": "TRANSFER",
            "status": "COMPLETED",
            "created_at": timezone.now() - timezone.timedelta(days=7),
        }
    )
    
    print("  ✅ Created test transactions")
else:
    print(f"  ℹ️  Test transactions already exist ({existing_count} transactions)")

print("\n" + "="*50)
print("Test Data Summary:")
print("="*50)
print(f"Staff User:      staff@test.com / testpass123")
print(f"Client 1:        client1@test.com / testpass123 (Balance: ${wallet1.balance})")
print(f"New Client:      newclient@test.com / testpass123 (NEW ACCOUNT)")
print(f"Receiver:        receiver@test.com / testpass123")
print(f"Total Transactions: {Transaction.objects.count()}")
print(f"Flagged Transactions: {Transaction.objects.filter(status='FLAGGED').count()}")
print("="*50)
EOF

print_success "Test data created successfully!"
echo ""

# --#-- Interactive Testing Menu
echo "Step 3: Testing Options"
echo "----------------------------------------------"
echo ""
echo "Choose a testing option:"
echo ""
echo "  1) Test Fraud Detection Rules"
echo "  2) Test Staff Dashboard"
echo "  3) Test Analytics Dashboard"
echo "  4) Run Automated Tests (pytest)"
echo "  5) Open Django Shell"
echo "  6) Start Development Server"
echo "  7) Start Celery Worker"
echo "  8) Exit"
echo ""

read -p "Enter choice (1-8): " choice

case $choice in
    1)
        echo ""
        echo "=============================================="
        echo "  Testing Fraud Detection Rules"
        echo "=============================================="
        echo ""
        print_info "Rule 1: Transfer > $10,000 should be flagged"
        print_info "Rule 2: > 5 transfers in 1 hour should be flagged"
        print_info "Rule 3: New account (> $1,000) should be flagged"
        echo ""
        
        $MANAGE shell --settings=$DJANGO_SETTINGS << 'EOF'
from accounts.models import CustomUser
from wallet.models import Wallet, Transaction
from wallet.services import transfer_funds
from decimal import Decimal

# Get users
client1 = CustomUser.objects.get(email="client1@test.com")
newclient = CustomUser.objects.get(email="newclient@test.com")
receiver = CustomUser.objects.get(email="receiver@test.com")

wallet1 = client1.client_profile.wallet
wallet2 = newclient.client_profile.wallet
receiver_wallet = receiver.client_profile.wallet

print("Testing Rule 1: Large Transfer (>$10,000)...")
print("-" * 50)
try:
    txn = transfer_funds(wallet1, receiver_wallet, Decimal("15000.00"), "Rule 1 Test")
    print(f"Transaction ID: {txn.id}")
    print(f"Status: {txn.status}")
    print(f"Flagged: {txn.metadata.get('flagged', False)}")
    if txn.status == "FLAGGED":
        print("✅ Rule 1 PASSED: Large transfer flagged!")
    else:
        print("❌ Rule 1 FAILED: Large transfer not flagged")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting Rule 3: New Account Transfer (>$1,000)...")
print("-" * 50)
try:
    txn = transfer_funds(wallet2, receiver_wallet, Decimal("1500.00"), "Rule 3 Test")
    print(f"Transaction ID: {txn.id}")
    print(f"Status: {txn.status}")
    print(f"Flagged: {txn.metadata.get('flagged', False)}")
    if txn.status == "FLAGGED":
        print("✅ Rule 3 PASSED: New account transfer flagged!")
    else:
        print("❌ Rule 3 FAILED: New account transfer not flagged")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting Rule 2: Frequent Transfers (>5 in 1 hour)...")
print("-" * 50)
print("Creating 6 rapid transfers...")
for i in range(6):
    try:
        txn = transfer_funds(wallet1, receiver_wallet, Decimal("100.00"), f"Rule 2 Test #{i+1}")
        print(f"  Transfer {i+1}: Status={txn.status}, Flagged={txn.metadata.get('flagged', False)}")
        if i == 5 and txn.status == "FLAGGED":
            print("✅ Rule 2 PASSED: 6th transfer flagged!")
    except Exception as e:
        print(f"  Transfer {i+1}: Error - {e}")

print("\n" + "="*50)
print("Flagged Transactions Summary:")
print("="*50)
flagged = Transaction.objects.filter(status="FLAGGED").order_by("-created_at")[:10]
for txn in flagged:
    print(f"ID: {txn.id} | Amount: ${txn.amount} | Type: {txn.type} | Reason: {txn.metadata.get('flag_reason', 'N/A')[:50]}")
print("="*50)
EOF
        ;;
    
    2)
        echo ""
        print_info "Staff Dashboard URL: http://localhost:8500/staff/dashboard/"
        print_info "Login: staff@test.com / testpass123"
        echo ""
        print_warning "Make sure the development server is running (Option 6)"
        echo ""
        read -p "Press Enter to open the URL in browser..."
        xdg-open "http://localhost:8500/staff/dashboard/" 2>/dev/null || open "http://localhost:8500/staff/dashboard/" 2>/dev/null || echo "Please open http://localhost:8500/staff/dashboard/ in your browser"
        ;;
    
    3)
        echo ""
        print_info "Analytics Dashboard URL: http://localhost:8500/analytics/dashboard/"
        print_info "Login: staff@test.com / testpass123"
        echo ""
        print_warning "Make sure the development server is running (Option 6)"
        echo ""
        read -p "Press Enter to open the URL in browser..."
        xdg-open "http://localhost:8500/analytics/dashboard/" 2>/dev/null || open "http://localhost:8500/analytics/dashboard/" 2>/dev/null || echo "Please open http://localhost:8500/analytics/dashboard/ in your browser"
        ;;
    
    4)
        echo ""
        echo "=============================================="
        echo "  Running Automated Tests"
        echo "=============================================="
        echo ""
        pytest operations/tests/ analytics/tests/ -v --tb=short --settings=$DJANGO_SETTINGS
        ;;
    
    5)
        echo ""
        echo "=============================================="
        echo "  Opening Django Shell"
        echo "=============================================="
        echo ""
        $MANAGE shell --settings=$DJANGO_SETTINGS
        ;;
    
    6)
        echo ""
        echo "=============================================="
        echo "  Starting Development Server"
        echo "=============================================="
        echo ""
        print_info "Server will start at: http://localhost:8500/"
        print_info "Press Ctrl+C to stop"
        echo ""
        $MANAGE runserver 8500 --settings=$DJANGO_SETTINGS
        ;;
    
    7)
        echo ""
        echo "=============================================="
        echo "  Starting Celery Worker"
        echo "=============================================="
        echo ""
        print_info "Celery worker will start processing tasks"
        print_info "Press Ctrl+C to stop"
        echo ""
        export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS
        celery -A core worker -l info
        ;;
    
    8)
        echo ""
        print_info "Exiting testing script"
        exit 0
        ;;
    
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
print_success "Testing complete!"
echo ""
