from datetime import date, timedelta
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Profile, Notification
from conferences.models import Department, Conference, ConferenceMaterial
from submissions.models import Submission
from registrations.models import Registration
from payments.models import Payment

TODAY = date.today()

# ---------------------------------------------------------------------------
# Indian demo data
# ---------------------------------------------------------------------------

DEPARTMENTS = [
    ("Computer Science & Engineering", "Algorithms, software engineering, artificial intelligence, and data science research."),
    ("Electronics & Communication Engineering", "VLSI design, signal processing, embedded systems, and telecommunications."),
    ("Mechanical Engineering", "Thermal sciences, robotics, manufacturing, and materials engineering."),
    ("Civil Engineering", "Structural engineering, transportation, environmental engineering, and construction management."),
    ("Electrical Engineering", "Power systems, control engineering, renewable energy, and electrical machines."),
    ("Information Technology", "Network security, cloud computing, IoT, and enterprise information systems."),
    ("Management", "Business analytics, operations management, finance, and organisational behaviour."),
]

ORGANIZERS = [
    "IEEE Student Branch, LJ University",
    "Department of Computer Science & Engineering, LJ University",
    "Department of Electronics & Communication Engineering, LJ University",
    "Department of Mechanical Engineering, LJ University",
    "Department of Civil Engineering, LJ University",
    "Department of Electrical Engineering, LJ University",
    "Department of Information Technology, LJ University",
    "LJ Institute of Management Studies",
]

CONFERENCE_TITLES = [
    "International Conference on Emerging Technologies and Innovation",
    "National Conference on Artificial Intelligence and Machine Learning",
    "International Conference on Sustainable Engineering",
    "National Symposium on IoT and Smart Systems",
    "Conference on Cyber Security and Digital Transformation",
    "Research Conference on Next Generation Computing",
    "International Conference on Renewable Energy and Power Systems",
    "National Conference on Structural Engineering and Advanced Materials",
    "CODE Technical Symposium on Software Engineering",
    "APEX National Conference on Robotics and Automation",
    "International Conference on Data Analytics and Business Intelligence",
    "National Workshop on Wireless Communication and Networks",
]

CONFERENCE_CODE_PREFIX = {
    "Computer Science & Engineering": "CSE",
    "Electronics & Communication Engineering": "ECE",
    "Mechanical Engineering": "ME",
    "Civil Engineering": "CE",
    "Electrical Engineering": "EE",
    "Information Technology": "IT",
    "Management": "MGT",
}

VENUES = [
    "LJ University Auditorium",
    "Seminar Hall, LJ University",
    "Main Conference Hall, LJ University",
    "Innovation & Research Centre, LJ University",
    "LJ Institute Convention Centre",
]

CITIES = ["Ahmedabad", "Gandhinagar", "Vadodara", "Surat", "Rajkot", "Mumbai", "Delhi", "Bengaluru", "Pune", "Chennai", "Hyderabad"]

INSTITUTIONS = [
    "LJ University, Ahmedabad",
    "Nirma University, Ahmedabad",
    "L.D. College of Engineering, Ahmedabad",
    "Gujarat Technological University, Ahmedabad",
    "Sardar Vallabhbhai National Institute of Technology, Surat",
    "Pandit Deendayal Energy University, Gandhinagar",
    "Maharaja Sayajirao University of Baroda, Vadodara",
    "Indian Institute of Technology, Gandhinagar",
    "CHARUSAT University, Anand",
    "Marwadi University, Rajkot",
    "Parul University, Vadodara",
    "Silver Oak University, Ahmedabad",
]

ABSTRACTS = [
    "This paper presents a novel approach to solving complex optimization problems using swarm intelligence algorithms, demonstrating improved convergence rates on benchmark functions relevant to Indian manufacturing datasets.",
    "We propose a deep learning framework for early detection of cardiovascular diseases from ECG signals, achieving 96% accuracy on a dataset collected from hospitals in Gujarat.",
    "This study investigates the mechanical properties of recycled aggregate concrete with partial replacement of cement by fly ash sourced from thermal power plants in Gujarat.",
    "A comprehensive analysis of smart grid integration with renewable energy sources is presented, addressing challenges in load balancing for the western Indian power grid.",
    "We introduce a blockchain-based supply chain management system ensuring transparency and traceability across multi-tier supplier networks for textile manufacturers in Surat.",
    "This research explores the application of IoT sensors for real-time structural health monitoring of bridges, reducing inspection costs and improving safety on Indian highways.",
    "An efficient routing protocol for vehicular ad hoc networks (VANETs) is proposed, minimising latency in dense urban environments such as Ahmedabad and Mumbai.",
    "We present a sentiment analysis model for regional-language social media data using transformer-based architectures, with applications to brand monitoring in Indian markets.",
    "This paper discusses the design and simulation of a microgrid system for rural electrification in Gujarat villages, integrating solar PV and battery storage.",
    "A study on the environmental impact of additive manufacturing processes proposes a framework for life-cycle assessment suitable for Indian small-scale industries.",
    "We develop a machine learning model for predicting student performance in online courses, achieving 88% prediction accuracy using behavioural and demographic features.",
    "An investigation into the use of geopolymer concrete as a sustainable alternative to Portland cement concrete, with testing across curing conditions typical of Indian summers.",
    "This work proposes a low-cost embedded system for water quality monitoring in rural water bodies, enabling early detection of contamination.",
    "We present a comparative study of financial risk models for Indian small and medium enterprises using machine learning based credit scoring.",
    "A novel antenna design for 5G communication systems is proposed and validated through simulation, targeted at dense urban Indian deployments.",
]

KEYWORDS = [
    "optimization, swarm intelligence, algorithms",
    "deep learning, ECG, healthcare",
    "recycled concrete, sustainability, fly ash",
    "smart grid, renewable energy, storage",
    "blockchain, supply chain, transparency",
    "IoT, structural health monitoring, bridges",
    "VANET, routing, latency",
    "NLP, sentiment analysis, social media",
    "microgrid, solar energy, rural electrification",
    "additive manufacturing, life-cycle assessment",
    "machine learning, education, prediction",
    "geopolymer, concrete, sustainability",
    "embedded systems, water quality, IoT",
    "machine learning, credit scoring, fintech",
    "5G, antenna design, wireless communication",
]

MALE_FIRST_NAMES = ["Aarav", "Harsh", "Dhruv", "Yash", "Krish", "Meet", "Rahul", "Kunal", "Vivek", "Aditya", "Nikhil", "Rohan", "Manav", "Parth", "Jay"]
FEMALE_FIRST_NAMES = ["Riya", "Priya", "Ananya", "Khushi", "Isha", "Diya", "Kavya", "Sneha", "Pooja", "Nisha", "Bhavya", "Shreya", "Aisha", "Meera", "Tanvi"]
LAST_NAMES = ["Patel", "Shah", "Mehta", "Desai", "Trivedi", "Joshi", "Parmar", "Vyas", "Chauhan", "Solanki", "Rana", "Thakor", "Bhatt", "Pandya", "Modi", "Gohil", "Yadav", "Iyer", "Nair", "Reddy"]

FACULTY_TITLES = ["Dr.", "Prof."]


def random_indian_name(gender=None):
    if gender is None:
        gender = random.choice(["M", "F"])
    first = random.choice(MALE_FIRST_NAMES if gender == "M" else FEMALE_FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return first, last


def random_indian_mobile():
    return f'{random.choice("6789")}{random.randint(10**8, 10**9 - 1)}'


class Command(BaseCommand):
    help = 'Create realistic Indian demo data for the Conference Management Tool.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating Indian demo data for CMT (LJ University)...'))

        # -----------------------------------------------------------------
        # Departments (create first so users/conferences can reference them)
        # -----------------------------------------------------------------
        departments = []
        for name, desc in DEPARTMENTS:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
            departments.append(dept)

        # -----------------------------------------------------------------
        # Core named users (admin / coordinator / author) per spec
        # -----------------------------------------------------------------
        admin_user = self._create_user(
            'admin', 'admin123', 'Rajesh', 'Patel', 'admin@cmt.edu.in',
            Profile.Role.ADMIN, institution='LJ University, Ahmedabad', is_superuser=True,
        )
        coord_user = self._create_user(
            'coordinator', 'coordinator123', 'Neha', 'Shah', 'neha.shah@cmt.edu.in',
            Profile.Role.COORDINATOR, institution='LJ University, Ahmedabad', department=departments[0],
        )
        author_user = self._create_user(
            'author', 'author123', 'Aarav', 'Mehta', 'aarav.mehta@gmail.com',
            Profile.Role.AUTHOR, institution='LJ University, Ahmedabad', department=departments[0],
        )

        # Assign a coordinator to every department (rotating through named faculty)
        for i, dept in enumerate(departments):
            if not dept.coordinator:
                fname, lname = random_indian_name()
                title = random.choice(FACULTY_TITLES)
                uname = f'{fname.lower()}.{lname.lower()}{i+1}'
                coord = self._create_user(
                    uname, 'coord123', f'{title} {fname}', lname, f'{uname}@cmt.edu.in',
                    Profile.Role.COORDINATOR, institution='LJ University, Ahmedabad', department=dept,
                )
                dept.coordinator = coord
                dept.save()

        # -----------------------------------------------------------------
        # Author / participant pool
        # -----------------------------------------------------------------
        named_authors = ["Riya Shah", "Harsh Patel", "Dhruv Joshi", "Priya Desai", "Yash Trivedi",
                          "Ananya Mehta", "Krish Patel", "Meet Shah", "Khushi Desai", "Rahul Parmar"]
        authors = [author_user]
        for full_name in named_authors:
            fname, lname = full_name.split(' ', 1)
            uname = f'{fname.lower()}.{lname.lower()}'
            u = self._create_user(
                uname, 'demo123', fname, lname, f'{uname}@gmail.com', Profile.Role.AUTHOR,
                institution=random.choice(INSTITUTIONS), department=random.choice(departments),
            )
            authors.append(u)
        # A few extra randomised authors for volume
        for i in range(10):
            fname, lname = random_indian_name()
            uname = f'{fname.lower()}.{lname.lower()}{i+1}'
            u = self._create_user(
                uname, 'demo123', fname, lname, f'{uname}@gmail.com', Profile.Role.AUTHOR,
                institution=random.choice(INSTITUTIONS), department=random.choice(departments),
            )
            authors.append(u)

        # -----------------------------------------------------------------
        # Conferences: 3 past, 3 current, 4 upcoming
        # -----------------------------------------------------------------
        conferences = []
        for i in range(3):
            dept = departments[i % len(departments)]
            c = self._create_conference(CONFERENCE_TITLES[i], dept,
                                         start=TODAY - timedelta(days=95 + i * 30),
                                         end=TODAY - timedelta(days=92 + i * 30))
            conferences.append(c)
        for i in range(3):
            dept = departments[(3 + i) % len(departments)]
            c = self._create_conference(CONFERENCE_TITLES[3 + i], dept,
                                         start=TODAY - timedelta(days=1),
                                         end=TODAY + timedelta(days=2))
            conferences.append(c)
        for i in range(4):
            dept = departments[(6 + i) % len(departments)]
            c = self._create_conference(CONFERENCE_TITLES[6 + i], dept,
                                         start=TODAY + timedelta(days=30 + i * 25),
                                         end=TODAY + timedelta(days=32 + i * 25))
            conferences.append(c)

        # -----------------------------------------------------------------
        # Conference materials (brochure + flyer for the first several)
        # -----------------------------------------------------------------
        from django.core.files.base import ContentFile
        for c in conferences[:6]:
            for mtype, label in [(ConferenceMaterial.MaterialType.BROCHURE, 'Brochure'),
                                  (ConferenceMaterial.MaterialType.FLYER, 'Flyer')]:
                ConferenceMaterial.objects.get_or_create(
                    conference=c,
                    material_type=mtype,
                    defaults={
                        'title': f'{c.title} - {label}',
                        'file': ContentFile(
                            f'Demo {label.lower()} for {c.title}, organised by {c.organizer}.'.encode(),
                            name=f'{c.pk}_{mtype.lower()}.txt',
                        ),
                        'uploaded_by': admin_user,
                    }
                )

        # -----------------------------------------------------------------
        # Paper submissions (~35)
        # -----------------------------------------------------------------
        submissions = []
        for i in range(35):
            author = random.choice(authors)
            conf = random.choice(conferences)
            ai = i % len(ABSTRACTS)
            ptype = random.choice(Submission.PresentationType.values)
            status = random.choice(Submission.Status.values)
            sub, created = Submission.objects.get_or_create(
                title=f'{ABSTRACTS[ai][:45]}... (Study {i+1})',
                author=author,
                conference=conf,
                defaults={
                    'abstract_text': ABSTRACTS[ai],
                    'keywords': KEYWORDS[ai],
                    'presentation_type': ptype,
                    'status': status,
                    'remarks': 'Reviewed by the technical programme committee.' if status != Submission.Status.SUBMITTED else '',
                }
            )
            if created:
                submissions.append(sub)

        # -----------------------------------------------------------------
        # Registrations (~28) with Indian mobile numbers
        # -----------------------------------------------------------------
        registrations = []
        for i in range(28):
            author = random.choice(authors)
            conf = random.choice(conferences)
            ptype = random.choice(Registration.ParticipantType.values)
            try:
                reg = Registration.objects.create(
                    user=author,
                    conference=conf,
                    participant_type=ptype,
                    phone=random_indian_mobile(),
                    institution=author.profile.institution or random.choice(INSTITUTIONS),
                    registration_fee=conf.registration_fee,
                    payment_status=Registration.PaymentStatus.PAID if i % 3 != 0 else Registration.PaymentStatus.PENDING,
                )
                registrations.append(reg)
            except Exception:
                pass  # Skip duplicates (unique_together on user/conference)

        # -----------------------------------------------------------------
        # Payments for paid registrations, amounts in INR
        # -----------------------------------------------------------------
        for reg in registrations:
            if reg.payment_status == Registration.PaymentStatus.PAID and not reg.payments.exists():
                Payment.objects.create(
                    registration=reg,
                    amount=reg.registration_fee,
                    status=Payment.PaymentStatus.PAID,
                    paid_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                )

        # -----------------------------------------------------------------
        # Notifications
        # -----------------------------------------------------------------
        for author in authors[:10]:
            Notification.objects.create(user=author, message='Your paper has been accepted for presentation.')
            Notification.objects.create(user=author, message='Your conference registration was successful.')
            if random.random() > 0.5:
                Notification.objects.create(user=author, message='Revision required for your submission. Please check remarks.')

        self.stdout.write(self.style.SUCCESS('Indian demo data created successfully!'))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Demo login credentials:'))
        self.stdout.write('  Admin (Dr. Rajesh Patel):       admin / admin123')
        self.stdout.write('  Coordinator (Prof. Neha Shah):  coordinator / coordinator123')
        self.stdout.write('  Author (Aarav Mehta):           author / author123')
        self.stdout.write('  (All other demo authors use password: demo123, department coordinators: coord123)')

    def _create_user(self, username, password, first, last, email, role, is_superuser=False, institution='', department=None):
        user, created = User.objects.get_or_create(username=username, defaults={
            'email': email, 'first_name': first, 'last_name': last,
            'is_superuser': is_superuser, 'is_staff': is_superuser,
        })
        if created:
            user.set_password(password)
            user.save()
            profile = user.profile
            profile.role = role
            profile.institution = institution or 'LJ University, Ahmedabad'
            profile.phone = random_indian_mobile()
            if department:
                profile.department = department
            profile.save()
        return user

    def _create_conference(self, title, department, start, end):
        prefix = CONFERENCE_CODE_PREFIX.get(department.name, 'GEN')
        seq = Conference.objects.filter(title=title).count() + 1
        code = f'CMT-{start.year}-{prefix}-{seq:03d}'
        city = random.choice(CITIES)
        organizer = random.choice(ORGANIZERS)
        conf, created = Conference.objects.get_or_create(title=title, defaults={
            'department': department,
            'description': (
                f'{title} is organised by {organizer} and brings together researchers, scholars, '
                f'and industry professionals from across India to present their latest work. '
                f'The conference features keynote talks, paper and poster presentation sessions, '
                f'and technical workshops held in {city}, Gujarat.'
            ),
            'start_date': start,
            'end_date': end,
            'venue': random.choice(VENUES),
            'organizer': organizer,
            'contact_email': f'{code.lower().replace("-", "")}@cmt.edu.in',
            'contact_phone': f'+91 {random.choice("6789")}{random.randint(10**8, 10**9 - 1)}',
            'registration_deadline': start - timedelta(days=15),
            'abstract_deadline': start - timedelta(days=30),
            'paper_deadline': start - timedelta(days=20),
            'registration_fee': random.choice([500, 750, 1000, 1200, 1500]),
            'is_published': True,
        })
        return conf
