from django.core.management.base import BaseCommand
import base64
import ecdsa

class Command(BaseCommand):
    help = 'Generate VAPID keys for push notifications'

    def generate_vapid_keypair(self):
        pk = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        vk = pk.get_verifying_key()
        private_key = base64.urlsafe_b64encode(pk.to_string()).rstrip(b'=').decode('utf-8')
        public_key = base64.urlsafe_b64encode(b'\x04' + vk.to_string()).rstrip(b'=').decode('utf-8')
        return {'private_key': private_key, 'public_key': public_key}

    def handle(self, *args, **options):
        try:
            vapid_keys = self.generate_vapid_keypair()
            
            self.stdout.write(self.style.SUCCESS('VAPID Keys Generated Successfully!'))
            self.stdout.write('')
            self.stdout.write('Add these to your environment variables:')
            self.stdout.write('')
            self.stdout.write(f'VAPID_PRIVATE_KEY={vapid_keys["private_key"]}')
            self.stdout.write(f'VAPID_PUBLIC_KEY={vapid_keys["public_key"]}')
            self.stdout.write('')
            self.stdout.write('Also update the vapidPublicKey in static/js/notifications.js:')
            self.stdout.write(f'vapidPublicKey: "{vapid_keys["public_key"]}"')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating VAPID keys: {e}')
            )