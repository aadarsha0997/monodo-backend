from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('referral_system', '0002_chatthread_chatmessage'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ChatMessage',
        ),
        migrations.DeleteModel(
            name='ChatThread',
        ),
    ]

