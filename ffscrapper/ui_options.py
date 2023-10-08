from PyQt6.QtWidgets import QCheckBox

def generate_breadth_search_options():
    """
    Generate scrape breadth options (category name to id mapping) for the UI table
    """

    scrape_breadth_options = {}
    scrape_breadth_options["men_shoes"] = {
        "checkbox": QCheckBox("Vyriška avalynė"),
        "category_id": "135968",
    }
    scrape_breadth_options["men_clothing"] = {
        "checkbox": QCheckBox("Vyriški drabužiai"),
        "category_id": "136330",
    }
    scrape_breadth_options["men_bags"] = {
        "checkbox": QCheckBox("Vyriškos rankinės"),
        "category_id": "135970",
    }
    scrape_breadth_options["men_accesories"] = {
        "checkbox": QCheckBox("Vyriški aksesuarai"),
        "category_id": "135972",
    }
    scrape_breadth_options["men_watches"] = {
        "checkbox": QCheckBox("Vyriški laikrodžiai"),
        "category_id": "137177",
    }

    scrape_breadth_options["women_shoes"] = {
        "checkbox": QCheckBox("Moteriška avalynė"),
        "category_id": "136301",
    }
    scrape_breadth_options["women_clothing"] = {
        "checkbox": QCheckBox("Moteriški drabužiai"),
        "category_id": "135967",
    }
    scrape_breadth_options["women_bags"] = {
        "checkbox": QCheckBox("Moteriškos rankinės"),
        "category_id": "135971",
    }
    scrape_breadth_options["women_accesories"] = {
        "checkbox": QCheckBox("Moteriški aksesuarai"),
        "category_id": "135973",
    }
    scrape_breadth_options["women_watches"] = {
        "checkbox": QCheckBox("Moteriški papuošalai"),
        "category_id": "135977",
    }

    scrape_breadth_options["baby_girls_shoes"] = {
        "checkbox": QCheckBox("Baby Girls avalynė"),
        "category_id": "136657",
    }
    scrape_breadth_options["baby_girls_clothing"] = {
        "checkbox": QCheckBox("Baby Girls rūbai"),
        "category_id": "136656",
    }
    scrape_breadth_options["baby_girls_accesories"] = {
        "checkbox": QCheckBox("Baby Girls aksesuarai"),
        "category_id": "136658",
    }
    scrape_breadth_options["baby_boys_shoes"] = {
        "checkbox": QCheckBox("Baby Boys avalynė"),
        "category_id": "136654",
    }
    scrape_breadth_options["baby_boys_clothing"] = {
        "checkbox": QCheckBox("Baby Boys rūbai"),
        "category_id": "136653",
    }
    scrape_breadth_options["baby_boys_accesories"] = {
        "checkbox": QCheckBox("Baby Boys aksesuarai"),
        "category_id": "136655",
    }

    scrape_breadth_options["kids_girls_shoes"] = {
        "checkbox": QCheckBox("Kids Girls avalynė"),
        "category_id": "136651",
    }
    scrape_breadth_options["kids_girls_clothing"] = {
        "checkbox": QCheckBox("Kids Girls rūbai"),
        "category_id": "136650",
    }
    scrape_breadth_options["kids_girls_accesories"] = {
        "checkbox": QCheckBox("Kids Girls aksesuarai"),
        "category_id": "136652",
    }
    scrape_breadth_options["kids_boys_shoes"] = {
        "checkbox": QCheckBox("Kids Boys avalynė"),
        "category_id": "136648",
    }
    scrape_breadth_options["kids_boys_clothing"] = {
        "checkbox": QCheckBox("Kids Boys rūbai"),
        "category_id": "136647",
    }
    scrape_breadth_options["kids_boys_accesories"] = {
        "checkbox": QCheckBox("Kids Boys aksesuarai"),
        "category_id": "136649",
    }

    scrape_breadth_options["teens_girls_shoes"] = {
        "checkbox": QCheckBox("Teens Girls avalynė"),
        "category_id": "136993",
    }
    scrape_breadth_options["teens_girls_clothing"] = {
        "checkbox": QCheckBox("Teens Girls rūbai"),
        "category_id": "136991",
    }
    scrape_breadth_options["teens_girls_accesories"] = {
        "checkbox": QCheckBox("Teens Girls aksesuarai"),
        "category_id": "136992",
    }
    scrape_breadth_options["teens_boys_shoes"] = {
        "checkbox": QCheckBox("Teens Boys avalynė"),
        "category_id": "136990",
    }
    scrape_breadth_options["teens_boys_clothing"] = {
        "checkbox": QCheckBox("Teens Boys rūbai"),
        "category_id": "136988",
    }
    scrape_breadth_options["teens_boys_accesories"] = {
        "checkbox": QCheckBox("Teens Boys aksesuarai"),
        "category_id": "136989",
    }

    return scrape_breadth_options