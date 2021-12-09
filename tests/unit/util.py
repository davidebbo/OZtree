import uuid

import sponsorship
import usernames

from gluon import current


def find_unsponsored_otts(count, in_reservations=None):
    db = current.db
    rows = sponsorship.sponsorable_children(
        1,    # 1st node should have all leaves as descendants
        qtype="id",
        limit=count,
        in_reservations=in_reservations)
    prices = {}
    for r in db(db.ordered_leaves.ott.belongs([r.ott for r in rows])).select(
        db.ordered_leaves.ott,
        db.ordered_leaves.price,
        db.banned.ott,
    ):
        prices[r.ordered_leaves.ott] = r

    if len(rows) < count:
        raise ValueError("Can't find available OTTs")
    rows = [r for r in rows if r.ott in prices and prices[r.ott].ordered_leaves.price > 0]
    if len(rows) < count:
        raise ValueError("Rows don't have associated prices set, visit /manage/SET_PRICES/")
    return [r.ott for r in rows]


def find_unsponsored_ott(in_reservations=None):
    return find_unsponsored_otts(1, in_reservations=in_reservations)[0]

def clear_unittest_sponsors():
    """
    Anything with UT:: id or basket_code, or @unittest.example.com e-mail address
    is assumed to be from a test, remove it
    """
    db = current.db
    db(
        db.reservations.user_registration_id.startswith('UT::') |
        db.reservations.basket_code.startswith('UT::') |
        db.reservations.e_mail.endswith('@unittest.example.com')).delete()
    db(
        db.expired_reservations.user_registration_id.startswith('UT::') |
        db.expired_reservations.basket_code.startswith('UT::') |
        db.expired_reservations.e_mail.endswith('@unittest.example.com')).delete()
    db(
        db.uncategorised_donation.basket_code.startswith('UT::') |
        db.uncategorised_donation.e_mail.endswith('@unittest.example.com')).delete()


def set_appconfig(section, key, val):
    """Update site config (section).(key) = (val)"""
    myconf = current.globalenv['myconf']
    myconf[section][key] = str(val)
    full_key = ".".join((section, key))
    if full_key in myconf.int_cache:
        del myconf.int_cache[full_key]


def set_allow_sponsorship(val):
    """Update site config with new value for sponsorship.allow_sponsorship"""
    set_appconfig('sponsorship', 'allow_sponsorship', val)

def set_maintenance_mins(val):
    """Update site config with new value for sponsorship.maintenance_mins"""
    set_appconfig('sponsorship', 'maintenance_mins', val)

def set_reservation_time_limit_mins(val):
    """Update site config with new value for sponsorship.reservation_time_limit_mins"""
    set_appconfig('sponsorship', 'reservation_time_limit_mins', val)


def purchase_reservation(otts = 1, basket_details = None, paypal_details = None, payment_amount = 10000, verify=True):
    """Go through all the motions required to purchase a reservation"""
    db = current.db

    purchase_uuid = uuid.uuid4()
    basket_code = 'UT::BK%s' % purchase_uuid

    if isinstance(otts, int):
        otts = [find_unsponsored_ott() for _ in range(otts)]

    if not basket_details:
        basket_details = {}
    if not paypal_details:
        paypal_details = {}
    if 'user_sponsor_name' not in basket_details:
        # Have to at least set user_sponsor_name
        basket_details['user_sponsor_name'] = basket_details.get("e_mail", "User %s" % purchase_uuid)
        basket_details['user_sponsor_kind'] = "by"
    if 'PP_transaction_code' not in paypal_details:
        paypal_details['PP_transaction_code'] = 'UT::PP%s' % purchase_uuid
    if 'PP_e_mail' not in paypal_details:
        paypal_details['PP_e_mail'] = "%s@paypal.unittest.example.com" % purchase_uuid
    if 'sale_time' not in paypal_details:
        paypal_details['sale_time'] = '01:01:01 Jan 01, 2001 GMT'

    for ott in otts:
        status, _, reservation_row, _ = sponsorship.get_reservation(ott, form_reservation_code="UT::%s" % purchase_uuid)
        assert status == 'available'
        sponsorship.reservation_add_to_basket(basket_code, reservation_row, basket_details)
    sponsorship.reservation_confirm_payment(basket_code, payment_amount, paypal_details)

    reservation_rows = db(db.reservations.basket_code == basket_code).select()
    if verify:
        for reservation_row in reservation_rows:
            verify_reservation(reservation_row)
    return reservation_rows


def verify_reservation(reservation_row):
    """Emulate verification logic in controllers/manage.py:SPONSOR_UPDATE"""
    # Add verified options
    reservation_row.update_record(
        verified_time=current.request.now,
        verified_kind=reservation_row.user_sponsor_kind,
        verified_name=reservation_row.user_sponsor_name,
        verified_donor_name=reservation_row.user_donor_name,
    )
    # Now verified details are set, map username
    username, _ = usernames.find_username(reservation_row)
    assert username
    reservation_row.update_record(
        username=username,
    )
