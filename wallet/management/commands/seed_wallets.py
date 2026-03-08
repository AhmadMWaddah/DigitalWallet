"""
Seed wallets management command.

Creates dummy client users with pre-funded wallets and random transaction history
for testing and demonstration purposes.
"""

import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from accounts.models import ClientProfile, UserType
from wallet.models import Transaction, Wallet
from wallet.services import deposit_funds, transfer_funds, withdraw_funds

CustomUser = get_user_model()


class Command(BaseCommand):
    """
    Seed wallets with dummy data.

    Creates multiple dummy client users with wallets and transaction history.
    """

    help = "Create dummy client users with pre-funded wallets and random transactions"

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            "--count",
            type=int,
            default=5,
            help="Number of dummy users to create (default: 5)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Purge existing dummy data before seeding",
        )
        parser.add_argument(
            "--prefix",
            type=str,
            default="testuser",
            help="Username prefix for dummy users (default: testuser)",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        count = options["count"]
        clear = options["clear"]
        prefix = options["prefix"]

        # -- Clear existing dummy data if requested
        if clear:
            self.clear_dummy_data(prefix)

        # -- Create dummy users
        self.stdout.write(f"Creating {count} dummy users...")
        users = []
        wallets = []

        for i in range(1, count + 1):
            email = f"{prefix}{i}@example.com"

            # Check if user already exists
            if CustomUser.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f"  User {email} already exists, skipping..."))
                continue

            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                password="testpass123",
                user_type=UserType.CLIENT,
                is_verified=True,
            )

            # Update profile
            user.client_profile.full_name = f"Test User {i}"
            user.client_profile.company = f"Test Company {i}"
            user.client_profile.save()

            # Create wallet with initial balance
            wallet = Wallet.objects.create(client_profile=user.client_profile)

            users.append(user)
            wallets.append(wallet)

            self.stdout.write(self.style.SUCCESS(f"  ✓ Created {email} with wallet"))

        # -- Fund wallets with initial deposits
        self.stdout.write("\nFunding wallets with initial deposits...")
        for wallet in wallets:
            initial_amount = Decimal(str(random.uniform(1000, 10000))).quantize(Decimal("0.01"))
            deposit_funds(
                wallet=wallet,
                amount=initial_amount,
                description="Initial seed funding",
                reference_id=f"SEED-INIT-{wallet.id}",
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ Funded {wallet.client_profile.user.email} with ${initial_amount:.2f}"
                )
            )

        # -- Create random transaction history
        self.stdout.write("\nCreating random transaction history...")
        transaction_count = 0

        for wallet in wallets:
            # Random number of transactions per wallet (5-15)
            num_transactions = random.randint(5, 15)

            for j in range(num_transactions):
                transaction_type = random.choice(["deposit", "withdraw", "transfer"])

                if transaction_type == "deposit":
                    amount = Decimal(str(random.uniform(50, 500))).quantize(Decimal("0.01"))
                    deposit_funds(
                        wallet=wallet,
                        amount=amount,
                        description=f"Seed deposit {j + 1}",
                        reference_id=f"SEED-DEP-{wallet.id}-{j}",
                    )
                    transaction_count += 1

                elif transaction_type == "withdraw":
                    # Only withdraw if balance is sufficient
                    if wallet.balance > 100:
                        max_withdraw = min(Decimal("100"), wallet.balance)
                        amount = Decimal(str(random.uniform(20, float(max_withdraw)))).quantize(
                            Decimal("0.01")
                        )
                        withdraw_funds(
                            wallet=wallet,
                            amount=amount,
                            description=f"Seed withdrawal {j + 1}",
                            reference_id=f"SEED-WDR-{wallet.id}-{j}",
                        )
                        transaction_count += 1

                elif transaction_type == "transfer" and len(wallets) > 1:
                    # Transfer to random other wallet
                    other_wallets = [w for w in wallets if w.id != wallet.id]
                    if other_wallets and wallet.balance > 50:
                        max_transfer = min(Decimal("50"), wallet.balance)
                        amount = Decimal(str(random.uniform(10, float(max_transfer)))).quantize(
                            Decimal("0.01")
                        )
                        receiver = random.choice(other_wallets)
                        transfer_funds(
                            sender_wallet=wallet,
                            receiver_wallet=receiver,
                            amount=amount,
                            description=f"Seed transfer {j + 1}",
                            reference_id=f"SEED-TRF-{wallet.id}-{receiver.id}-{j}",
                        )
                        transaction_count += 1

        # -- Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Seed completed successfully!"))
        self.stdout.write(f"\n  Users created: {len(users)}")
        self.stdout.write(f"  Wallets funded: {len(wallets)}")
        self.stdout.write(f"  Transactions created: {transaction_count}")
        self.stdout.write("\n  All users have password: testpass123")
        self.stdout.write("=" * 60)

    def clear_dummy_data(self, prefix):
        """Clear existing dummy data."""
        self.stdout.write("Clearing existing dummy data...")

        # Delete transactions for dummy wallets
        dummy_users = CustomUser.objects.filter(email__startswith=prefix)
        dummy_profiles = ClientProfile.objects.filter(user__in=dummy_users)
        dummy_wallets = Wallet.objects.filter(client_profile__in=dummy_profiles)

        # Delete transactions
        Transaction.objects.filter(wallet__in=dummy_wallets).delete()
        Transaction.objects.filter(counterparty_wallet__in=dummy_wallets).delete()

        # Delete wallets
        Wallet.objects.filter(client_profile__in=dummy_profiles).delete()

        # Delete users (profiles deleted via cascade)
        deleted_count, _ = CustomUser.objects.filter(email__startswith=prefix).delete()

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Cleared {deleted_count} dummy users and related data")
        )
