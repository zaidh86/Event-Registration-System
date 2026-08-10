import threading

from django.db import connections
from django.test import TransactionTestCase

from common.exceptions import Conflict
from events.models import Category, EventStatus
from events.tests.helpers import create_attendee, create_event, create_organizer
from registrations import services
from registrations.models import Registration, RegistrationStatus


class ConcurrentRegistrationTests(TransactionTestCase):
    """Exercises the real select_for_update locking across DB connections.

    TransactionTestCase commits to the database, so each thread's own
    connection observes the others' transactions — unlike TestCase, which
    would keep everything inside one invisible transaction.
    """

    def test_concurrent_registrations_cannot_exceed_capacity(self):
        organizer = create_organizer()
        category = Category.objects.create(name="Concurrency")
        event = create_event(
            organizer, status=EventStatus.PUBLISHED, capacity=2, category=category
        )
        attendees = [create_attendee(f"attendee{i}@example.com") for i in range(5)]

        barrier = threading.Barrier(len(attendees))
        outcomes = []
        outcomes_lock = threading.Lock()

        def attempt(user):
            barrier.wait()
            try:
                services.register_for_event(user=user, event_id=event.id)
                outcome = "registered"
            except Conflict as exc:
                outcome = exc.detail.code
            except Exception as exc:  # pragma: no cover - diagnostic aid
                outcome = repr(exc)
            finally:
                connections.close_all()
            with outcomes_lock:
                outcomes.append(outcome)

        threads = [threading.Thread(target=attempt, args=(user,)) for user in attendees]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        confirmed = Registration.objects.filter(
            event=event, status=RegistrationStatus.CONFIRMED
        ).count()
        self.assertEqual(confirmed, 2)
        self.assertEqual(outcomes.count("registered"), 2, outcomes)
        self.assertEqual(outcomes.count("event_full"), 3, outcomes)
