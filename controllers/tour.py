# -*- coding: utf-8 -*-
"""
Endpoints relating to editing Tours
"""
from OZfunc import (
    add_the,
    get_common_name, get_common_names,
    nice_name,
)


def homepage_animation():
    # OTTs from the tree_startpoints table
    startpoints_ott_map, hrefs, titles, text_titles = {}, {}, {}, {}
    carousel, anim, threatened = [], [], []
    for r in db(
            (db.tree_startpoints.category.startswith('homepage')) &
            (db.tree_startpoints.partner_identifier == None)
        ).select(
            db.tree_startpoints.ott, db.tree_startpoints.category,
            db.tree_startpoints.image_url, db.tree_startpoints.tour_identifier,
            orderby = db.tree_startpoints.id):
        key = r.tour_identifier or str(r.ott)
        if r.category.endswith("main"):
            carousel.append(key)
        elif r.category.endswith("anim"):
            anim.append(key)
        elif r.category.endswith("red"):
            threatened.append(key)
        if r.tour_identifier:
            hrefs[key] = URL('life/' + r.tour_identifier)
            title = db(db.tours.identifier == r.tour_identifier).select(db.tours.name).first()
            text_titles[key] = title.name if title else r.tour_identifier
        else:
            text_titles[key] = ""
        if r.ott:
            # We might still want to find e.g. an image, even if we are looking at a tour
            startpoints_ott_map[r.ott] = key

    # Names
    st_node_otts, has_vernacular = set(), set()
    # Look up scientific names for startpoint otts
    for r in db(db.ordered_leaves.ott.belongs(startpoints_ott_map.keys())).select(
            db.ordered_leaves.ott, db.ordered_leaves.name):
        titles[r.ott] = r.name
    # Look up scientific names and best PD image otts for all startpoint otts
    for r in db(db.ordered_nodes.ott.belongs(list(startpoints_ott_map.keys()))).select(
            db.ordered_nodes.ott, db.ordered_nodes.name, db.ordered_nodes.rpd1):
        st_node_otts.add(r.ott)
        titles[r.ott] = r.name
    # Add or change to vernacular names in the titles
    for ott, vn in get_common_names(titles.keys(), return_nulls=True).items():
        # Do one thing for the startpoints (simple names) ...
        startpoint_key = startpoints_ott_map.get(ott, None)
        if startpoint_key:
            if not text_titles[startpoint_key]:
                if vn is not None:
                    has_vernacular.add(startpoint_key)
                text_titles[startpoint_key] = nice_name(
                    (titles[ott] if vn is None else None), vn, html=True,
                    is_species=ott not in st_node_otts, break_line=2)
        # ... and another for the sponsored items (both common and sci in the string)
        if vn is not None:
            has_vernacular.add(ott)
        titles[ott] = nice_name(
            titles[ott], vn, html=True, is_species=ott not in st_node_otts,
            first_upper=True, break_line=1)
    titles.update(text_titles)

    return dict(
        anim=anim,
        hrefs=hrefs,
        has_vernacular=has_vernacular,
        html_names=titles,
        add_the=add_the,
    )


def tutorial_MDmouse():
    """Mouse variant of museum display tutorial"""
    response.view = request.controller + "/tutorial_MD." + request.extension
    return dict()


def tutorial_MDtouch():
    """Touch variant of museum display tutorial"""
    response.view = request.controller + "/tutorial_MD." + request.extension
    return dict()


def screensaver():
    """Screensaver tour"""
    return dict(
        screensaver_otts=[991547, 81461, 99252, 770315],
    )


def data():
    """Fetch generic tour name from database"""
    if len(request.args) < 1:
        raise ValueError("Expect a tour identifier at the end of the URL")
    tour_identifier = request.args[0]

    if request.env.request_method == 'PUT':
        # Need to be logged in before you can create tours
        auth.basic()
        if not auth.user:
            return HTTP(403)
        if len(request.vars.get('tourstops', [])) == 0:
            raise ValueError("Must have at least one tourstop")

        # Check that tourstop identifiers are unique within the tour
        # TODO: Ideally we'd make a DB constraint for this, but is beyond the abilities of PyDAL
        ts_identifiers = set(ts['identifier'] for ts in request.vars['tourstops'])
        if len(ts_identifiers) != len(request.vars['tourstops']):
            raise ValueError("All tourstops should have a unique identifier")

        # Upsert the tour data
        db.tour.update_or_insert(
            db.tour.identifier == tour_identifier,
            identifier=tour_identifier,
            lang=request.vars.get('lang', 'en'),
            author=request.vars.get('author'),
            image_url=request.vars.get('image_url'),
            title=request.vars.get('title'),
            description=request.vars.get('description'),
            keywords=request.vars.get('keywords'),
        )
        tour_id = db.tour(db.tour.identifier == tour_identifier).id

        # Remove any no-longer extant tourstops
        db(db.tourstop.tour == tour_id & ~db.tourstop.identifier.belongs(ts_identifiers)).delete()

        # Upsert each tourstop
        ts_shared = request.vars.get('tourstop_shared', {})
        for i, ts in enumerate(request.vars['tourstops']):
            ts = { **ts_shared, **ts, "tour": tour_id, "ord": i + 1 }  # Combine with shared data, references
            if 'symlink' in ts:
                raise ValueError("TODO: Insert a symlink tourstop with ord i + 1")
            else:
                db.tourstop.update_or_insert(
                    (db.tourstop.tour == tour_id) & (db.tourstop.identifier == ts['identifier']),
                    **ts,
                )

    # Fetch tour from DB
    tour = db(db.tour.identifier == tour_identifier).select()
    if len(tour) < 1:
        raise HTTP(404)
    tour = tour[0]

    # Fetch associated tourstops
    tourstops = tour.tourstop.select(orderby=db.tourstop.ord)
    tourstop_symlinks = tour.tourstop_symlink.select(orderby=db.tourstop.ord)

    if len(tourstop_symlinks) > 0:
        raise ValueError("TODO: Combine 2 lists of tourstops according to ord")

    # Reconstitute tour JSON
    def munge_tourstop(ts):
        if ts.secondary_ott:
            ts.ott = "%d..%d" % (ts.ott, ts.secondary_ott)
        return ts
    tour['tourstops'] = [munge_tourstop(t) for t in tourstops]
    return dict(
        tour_identifier=tour_identifier,
        tour=tour,
    )
