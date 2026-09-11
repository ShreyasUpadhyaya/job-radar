"""Emit companies.yml from the full screenshot set.

tier:     noida | india | global   (global must hire remote into India)
priority: 1 = read every day. 2 = read on Sundays if the portal needs
          rendering, since Firecrawl credits are finite. Portals with a free
          API are always read daily whatever the priority.
"""

# (name, careers-or-site url, tier, priority)
NOIDA_NCR = [
    ("Ace Turtle", "https://aceturtle.com/careers", "noida", 1),
    ("Advanz 101", "https://www.advanz101.com/careers/", "noida", 2),
    ("AgroStar", "https://agrostar.in/careers", "india", 2),
    ("Aikonic", "https://aikonic.com/", "noida", 2),
    ("Amber", "https://amberstudent.com/careers", "noida", 2),
    ("ApnaKlub", "https://www.apnaklub.com/careers", "india", 2),
    ("Appinventiv", "https://appinventiv.com/career/", "noida", 1),
    ("Auxilo Finserve", "https://www.auxilo.com/careers", "india", 2),
    ("Awign", "https://www.awign.com/careers", "india", 2),
    ("Bijnis", "https://bijnis.com/careers", "noida", 1),
    ("boAt", "https://www.boat-lifestyle.com/pages/careers", "india", 2),
    ("CashKaro", "https://cashkaro.com/careers", "noida", 1),
    ("ClearTax", "https://cleartax.in/s/careers", "india", 1),
    ("Cropin", "https://www.cropin.com/careers", "india", 1),
    ("Delhivery", "https://www.delhivery.com/company/careers", "noida", 1),
    ("Droom", "https://droom.in/careers", "noida", 1),
    ("EaseMyTrip", "https://www.easemytrip.com/careers.html", "noida", 1),
    ("Edaify", "https://edaify.com/", "noida", 2),
    ("FarMart", "https://www.farmart.co/careers", "noida", 1),
    ("FlexiLoans", "https://flexiloans.com/careers", "india", 2),
    ("Khatabook", "https://khatabook.com/hiring/", "india", 1),
    ("Learnovate", "https://learnovate.co.in/", "noida", 2),
    ("Meesho", "https://www.meesho.io/jobs", "india", 1),
    ("Moglix", "https://www.moglix.com/careers", "noida", 1),
    ("NeoKred", "https://neokred.tech/careers", "india", 2),
    ("NoBroker", "https://www.nobroker.in/careers", "india", 1),
    ("OfBusiness", "https://ofbusiness.com/careers", "noida", 1),
    ("PharmEasy", "https://pharmeasy.in/careers", "india", 2),
    ("Pine Labs", "https://www.pinelabs.com/careers", "noida", 1),
    ("Policybazaar", "https://careers.policybazaar.com/", "noida", 1),
    ("Razorpay", "https://razorpay.com/careers/", "india", 1),
    ("redBus", "https://www.redbus.in/info/careers", "india", 1),
    ("Rivigo", "https://rivigo.com/careers/", "noida", 2),
    ("Shiprocket", "https://www.shiprocket.in/careers/", "noida", 1),
    ("Slice", "https://www.sliceit.com/careers", "india", 1),
    ("Spenmo", "https://spenmo.com/careers", "global", 2),
    ("Udaan", "https://careers.udaan.com/", "india", 1),
    ("Unacademy", "https://unacademy.com/careers", "india", 1),
    ("Urban Company", "https://www.urbancompany.com/careers/", "india", 1),
    ("Velocity", "https://velocity.in/careers", "india", 2),
    ("Vezdo", "https://vezdo.com/", "noida", 2),
    ("Walnut", "https://walnut.education/", "noida", 2),
    ("WhiteHat Jr", "https://www.whitehatjr.com/careers", "india", 2),
    ("WinZO", "https://www.winzogames.com/careers", "noida", 1),
    ("Writer", "https://writer.com/company/careers/", "global", 1),
    ("Yubi", "https://www.go-yubi.com/careers/", "india", 1),
    ("Zapak", "https://www.zapak.com/", "noida", 2),
    ("Zetwerk", "https://www.zetwerk.com/careers/", "india", 1),
    ("Zopper", "https://www.zopper.com/careers", "noida", 1),
    ("Zypp Electric", "https://zypp.app/careers", "noida", 1),
]

INDIA_SAAS = [
    ("BrowserStack", "https://www.browserstack.com/careers", "india", 1),
    ("Postman", "https://www.postman.com/company/careers/", "india", 1),
    ("Zoho", "https://careers.zohocorp.com/jobs", "india", 1),
    ("Freshworks", "https://www.freshworks.com/company/careers/", "india", 1),
    ("Chargebee", "https://www.chargebee.com/careers/", "india", 1),
    ("Hasura", "https://hasura.io/careers", "india", 1),
    ("Atlan", "https://atlan.com/careers/", "india", 1),
    ("Wingify", "https://wingify.com/careers/", "noida", 1),
    ("GitLab", "https://about.gitlab.com/jobs/", "global", 1),
    ("Canonical", "https://canonical.com/careers", "global", 1),
    ("PhonePe", "https://www.phonepe.com/careers/", "india", 1),
    ("CRED", "https://careers.cred.club/", "india", 1),
    ("Groww", "https://groww.in/careers", "india", 1),
    ("Zerodha", "https://careers.zerodha.com/", "india", 1),
    ("Zeta", "https://www.zeta.tech/careers", "india", 1),
    ("Jupiter", "https://jupiter.money/careers/", "india", 1),
    ("Deel", "https://www.deel.com/careers/", "global", 1),
    ("Remote", "https://remote.com/careers", "global", 1),
    ("Automattic", "https://automattic.com/work-with-us/", "global", 1),
    ("Turing", "https://www.turing.com/careers", "global", 1),
    ("Buffer", "https://buffer.com/journey", "global", 1),
    ("Doist", "https://doist.com/careers", "global", 1),
    ("Zapier", "https://zapier.com/jobs", "global", 1),
    ("Shopify", "https://www.shopify.com/careers", "global", 1),
    ("Elastic", "https://www.elastic.co/careers", "global", 1),
    ("Coinbase", "https://www.coinbase.com/careers", "global", 1),
    ("Miro", "https://miro.com/careers/", "global", 1),
    ("Cloudflare", "https://www.cloudflare.com/careers/", "global", 1),
]

# The 30+ LPA list. Consulting and PE rarely want an ML engineer, but the
# product and quant names on that list very much do.
HIGH_PAY_INDIA = [
    ("Amazon", "https://www.amazon.jobs/en/", "india", 1),
    ("Google", "https://www.google.com/about/careers/applications/", "india", 1),
    ("Microsoft", "https://jobs.careers.microsoft.com/global/en/search", "india", 1),
    ("Adobe", "https://careers.adobe.com/us/en/search-results", "india", 1),
    ("Uber", "https://www.uber.com/us/en/careers/list/", "india", 1),
    ("Salesforce", "https://careers.salesforce.com/en/jobs/", "india", 1),
    ("D.E. Shaw", "https://www.deshawindia.com/careers", "india", 1),
    ("Goldman Sachs", "https://www.goldmansachs.com/careers/", "india", 2),
    ("Morgan Stanley", "https://www.morganstanley.com/careers", "india", 2),
    ("JPMorgan", "https://careers.jpmorgan.com/global/en/home", "india", 2),
    ("American Express", "https://www.americanexpress.com/en-us/careers/", "india", 2),
    ("Mastercard", "https://careers.mastercard.com/us/en", "india", 2),
    ("Visa", "https://usa.visa.com/careers.html", "india", 2),
    ("Flipkart", "https://www.flipkartcareers.com/", "india", 1),
    ("Myntra", "https://careers.myntra.com/", "india", 1),
    ("Eternal (Zomato)", "https://www.zomato.com/careers", "india", 1),
    ("Swiggy", "https://careers.swiggy.com/", "india", 1),
    ("Navi", "https://navi.com/careers", "india", 1),
    ("Reliance", "https://careers.ril.com/", "india", 2),
    ("Aditya Birla Group", "https://careers.adityabirla.com/", "india", 2),
    ("ITC", "https://www.itcportal.com/careers/", "india", 2),
    ("P&G", "https://www.pgcareers.com/", "india", 2),
    ("HUL", "https://www.unilever.com/careers/", "india", 2),
    ("McKinsey", "https://www.mckinsey.com/careers/search-jobs", "india", 2),
    ("BCG", "https://careers.bcg.com/", "india", 2),
    ("Bain", "https://www.bain.com/careers/", "india", 2),
    ("EY-Parthenon", "https://www.ey.com/en_in/careers", "india", 2),
    ("Kearney", "https://www.kearney.com/careers", "india", 2),
    ("Oliver Wyman", "https://www.oliverwyman.com/careers.html", "india", 2),
    ("Alvarez & Marsal", "https://www.alvarezandmarsal.com/careers", "india", 2),
    ("Blackstone", "https://www.blackstone.com/careers/", "india", 2),
    ("Avendus", "https://www.avendus.com/india/careers", "india", 2),
    ("General Atlantic", "https://www.generalatlantic.com/careers/", "india", 2),
    ("Jefferies", "https://www.jefferies.com/careers/", "india", 2),
    ("Kotak Mahindra Capital", "https://www.kotak.com/en/careers.html", "india", 2),
    ("Deutsche Bank", "https://careers.db.com/", "india", 2),
    ("UBS", "https://www.ubs.com/global/en/careers.html", "india", 2),
    ("Barclays", "https://home.barclays/careers/", "india", 2),
    ("Bank of America", "https://careers.bankofamerica.com/", "india", 2),
]

# Recruitment agencies from the agency screenshot. They post client roles, so
# they widen coverage, but the noise is higher.
AGENCIES = [
    ("Talent500", "https://talent500.com/jobs", "india", 1),
    ("Randstad India", "https://www.randstad.in/jobs/", "india", 2),
    ("ABC Consultants", "https://www.abcconsultants.in/apply/", "india", 2),
    ("Michael Page India", "https://www.michaelpage.co.in/jobs", "india", 2),
    ("CareerNet Consulting", "https://careernet.in/", "india", 2),
    ("Xpheno", "https://www.xpheno.com/", "india", 2),
    ("CIEL HR Services", "https://www.cielhr.com/", "india", 2),
    ("PeopleStrong", "https://www.peoplestrong.com/", "india", 2),
    ("Crescendo Global", "https://crescendo-global.com/jobs/", "india", 2),
    ("Hays India", "https://www.hays.co.in/job-search", "india", 2),
    ("Korn Ferry", "https://www.kornferry.com/careers", "india", 2),
    ("Antal International India", "https://www.antal.com/jobs", "india", 2),
    ("PERSOLKELLY India", "https://www.persolindia.com/", "india", 2),
    ("Kelly Services India", "https://www.kellyservices.co.in/", "india", 2),
    ("FirstMeridian", "https://www.firstmeridian.com/", "india", 2),
    ("Innovsource", "https://www.innovsource.com/", "india", 2),
    ("WalkWater Talent Advisors", "https://www.walkwater.com/", "india", 2),
    ("Head Field Solutions", "https://www.headfield.com/", "india", 2),
    ("Quadrangle", "https://www.quadrangle.in/", "india", 2),
    ("Sutra HR", "https://www.sutrahr.com/", "india", 2),
    ("Multi Recruit", "https://www.multirecruit.com/", "india", 2),
    ("Adhaan Solutions", "https://www.adhaan.com/", "india", 2),
    ("Alliance International", "https://www.allianceinternational.co.in/", "india", 2),
    ("Alliance Recruitment Agency", "https://www.alliancerecruitmentagency.com/", "india", 2),
    ("WorkSource Consultants", "https://worksourceconsultant.in/", "india", 2),
    ("GI Group Holding India", "https://www.gigroup.com/", "india", 2),
    ("Spencer Stuart India", "https://www.spencerstuart.com/careers", "india", 2),
    ("Heidrick & Struggles India", "https://www.heidrick.com/", "india", 2),
    ("PlacementIndia", "https://www.placementindia.com/", "india", 2),
]

# The A-Z remote-friendly spreadsheet. Domains are exactly as shown in the
# screenshots; the resolver finds each one's careers path.
GLOBAL_REMOTE = """
10up|10up.com|1
15Five|15five.com|2
17hats|17hats.com|2
1Password|1password.com|1
42 Technologies|42technologies.com|2
abiturma|abiturma.de|2
Ably|ably.io|1
Abstract API|abstractapi.com|2
acct|acct.global|2
Acivilate|acivilate.com|2
Acquia|acquia.com|2
ActiveCampaign|activecampaign.com|2
Ad Hoc|adhocteam.us|2
Adaface|adaface.com|1
AddStructure|bazaarvoice.com|2
Adeva|adevait.com|1
Adzuna|adzuna.co.uk|2
AE Studio|ae.studio|1
Aerolab|aerolab.co|2
Aerostrat|aerostratsoftware.com|2
AgFlow|agflow.com|2
Aha!|aha.io|2
Aim India|aimincorp.com|2
Airbank|joinairbank.com|2
Airbyte|airbyte.com|1
AirGarage|airgarage.com|2
AirTreks|airtreks.com|2
Aivitex|aivitex.com|2
Alami|alamisharia.co.id|2
Axelerant|axelerant.com|1
Axios|axios.com|2
BairesDev|bairesdev.com|1
Balena|balena.io|1
Balsamiq|balsamiq.com|2
Bandcamp|bandcamp.com|2
BandLab|bandlab.com|2
Bandzoogle|bandzoogle.com|2
Baremetrics|baremetrics.com|2
Basecamp|basecamp.com|2
Bear Group|beargroup.com|2
BeBanjo|bebanjo.com|2
BeenVerified|beenverified.com|2
Best Practical|bestpractical.com|2
Betable|corp.betable.com|2
BetaPeak|betapeak.com|2
BetterUp|betterup.com|2
Beyond Company|beyondcompany.com.br|2
BeyondPricing|beyondpricing.com|2
Big Cartel|bigcartel.com|2
Bill|bill.com|2
Bit Zesty|bitzesty.com|2
Bitnami|bitnami.com|2
Bitovi|bitovi.com|1
Bizink|bizinkonline.com|2
Blameless|blameless.com|2
Bloc|bloc.io|2
BlueCat Networks|bluecatnetworks.com|2
Chef|chef.io|2
ChefsClub|chefsclub.com.br|2
Chess.com|chess.com|1
Chroma|trychroma.com|1
CircleCI|circleci.com|1
Circonus|circonus.com|2
CivicActions|civicactions.com|2
Civo|civo.com|1
Clevertech|clevertech.biz|1
ClickUp|clickup.com|1
Clootrack|clootrack.com|1
Close|close.com|1
CloudApp|getcloudapp.com|2
Coalition Technologies|coalitiontechnologies.com|2
Code Like a Girl|codelikeagirl.com|2
Codea IT|codeait.com|2
CodePen|codepen.io|2
CodeSandbox|codesandbox.io|1
Codeship|codeship.com|2
Codestunts|codestunts.com|2
Cofense|cofense.com|2
Coingape|coingape.com|2
Collabora|collabora.com|1
Comet|comet.co|2
Compose|compose.io|2
Compucorp|compucorp.co.uk|2
Connexa|connexa.com|2
Continu|continu.co|2
Conversio|conversio.com|2
Convert|convert.com|2
Coodesh|coodesh.com|2
Core-Apps|core-apps.com|2
CoreOS|coreos.com|2
Corgibytes|corgibytes.com|2
Coursera|coursera.org|1
Crossover|crossover.com|1
CrowdStrike|crowdstrike.com|1
CrowdTangle|crowdtangle.com|2
Cueup|cueup.io|2
Customer.io|customer.io|1
Cuvette|cuvette.tech|1
CVS Health|jobs.cvshealth.com|2
CWT|mycwt.com|2
Cyber Whale|cyberwhale.tech|2
Dalenys|dalenys.com|2
DappRadar|dappradar.com|2
DareCode|darecode.com|2
DashboardHub|dashboardhub.io|2
Dashlane|dashlane.com|2
Data Science Brigade|dsbrigade.com|1
Data Science Dojo|datasciencedojo.com|1
DataCamp|datacamp.com|1
Datadog|datadoghq.com|1
DataStax|datastax.com|1
Datica|datica.com|2
DealDash|dealdash.com|2
Deskpass|deskpass.com|2
Dev Spotlight|devspotlight.com|2
Devsquad|devsquad.com|2
Dgraph|dgraph.io|1
DigitalOcean|digitalocean.com|1
Discord|discord.com|1
Discourse|discourse.org|1
DNSimple|dnsimple.com|2
Docker|docker.com|1
Donut App|donut.app|2
DroneDeploy|dronedeploy.com|1
Dropbox|dropbox.com|1
Drupal Jedi|drupaljedi.com|2
DuckDuckGo|duckduckgo.com|1
DynaPictures|dynapictures.com|2
EarthOfDrones|earthofdrones.com|1
EatStreet|eatstreet.com|2
EBSCO Information Services|ebsco.com|2
Eco-Mind|eco-mind.eu|2
Edgar|meetedgar.com|2
Edgio|edg.io|2
Edify|edify.cr|2
eFishery|efishery.com|2
Emsisoft|emsisoft.com|2
EngineYard|engineyard.com|2
Enok|enok.co|2
Entrision|entrision.com|2
Envato|envato.com|1
Envoy|envoy.com|2
EPAM|epam.com|1
Epic Games|epicgames.com|1
Epilocal|epilocal.com|2
Episource|episource.com|2
Equal Experts|equalexperts.com|1
Ergeon|ergeon.com|2
Estately|estately.com|2
Etch|etch.co|2
Etsy|etsy.com|1
EVELO|evelo.com|2
Evil Martians|evilmartians.com|1
Evrone|evrone.com|1
ExportData|exportdata.io|2
Eyeo|eyeo.com|2
FactorialHR|factorialhr.com|2
Fairwinds|fairwinds.com|2
Faithlife|faithlife.com|2
Fastly|fastly.com|1
FATMAP|about.fatmap.com|2
Fauna|fauna.com|1
Featurist|featurist.co.uk|2
FFW Agency|ffwagency.com|2
Filament Group|filamentgroup.com|2
FingerprintJS|fingerprint.com|1
Fire Engine Red|fire-engine-red.com|2
Fireball Labs|fireballlabs.com|2
Fiverr|fiverr.com|1
FivexL|fivexl.io|2
Flexera|flexera.com|2
FlightAware|flightaware.com|2
Flip|flip.id|2
Flowing|flowing.it|2
Fly.io|fly.io|1
FMX|gofmx.com|2
Focusnetworks|focusnetworks.com.br|2
fohandboh|fohandboh.com|2
Formidable|formidable.com|2
Formstack|formstack.com|1
Four Kitchens|fourkitchens.com|2
Fraudio|fraudio.com|2
FreeAgent|freeagent.com|2
Freeletics|freeletics.com|2
Fuel Made|fuelmade.com|2
FullFabric|fullfabric.com|2
Functionize|functionize.com|2
Gaggle|gaggle.net|2
Geckoboard|geckoboard.com|2
General Assembly|generalassemb.ly|2
GEO Jobe|geo-jobe.com|2
Gerencianet|gerencianet.com.br|2
GFT|gft.com|1
Ghost Foundation|ghost.org|2
Ghost Inspector|ghostinspector.com|2
Grafana Labs|grafana.com|1
Sourcegraph|sourcegraph.com|1
"""

# From remoteatlas.app. Only companies whose own listings name India inside the
# hiring scope: most of that board is US-locked or EU-locked remote, which the
# location rule rejects anyway.
REMOTE_ATLAS = [
    ("Everis", "https://everis.com/careers", "global", 1),
    ("Retell AI", "https://www.retellai.com/careers", "global", 1),
    ("Storyblok", "https://www.storyblok.com/careers", "global", 1),
    ("MinIO", "https://min.io/careers", "global", 1),
]


def emit():
    rows = []
    for group in (NOIDA_NCR, INDIA_SAAS, HIGH_PAY_INDIA, AGENCIES, REMOTE_ATLAS):
        rows.extend(group)
    for line in GLOBAL_REMOTE.strip().splitlines():
        name, domain, pri = line.split("|")
        rows.append((name, f"https://{domain}", "global", int(pri)))

    seen, out = set(), []
    for name, url, tier, pri in rows:
        if name in seen:
            continue
        seen.add(name)
        out.append(f'  - {{name: "{name}", tier: {tier}, priority: {pri}, careers: "{url}"}}')

    header = (
        "# Job Radar company registry, generated by tools/build_registry.py\n"
        "#\n"
        "# Every company here comes from the screenshots. `careers` is the company's\n"
        "# own page; where it is a bare domain the resolver finds the careers path.\n"
        "# Leave `ats` unset and the resolver works out what the portal runs on.\n"
        "#\n"
        "# tier:     noida | india | global (global must hire remote into India)\n"
        "# priority: 1 = read daily. 2 = rendered portals read on Sundays only,\n"
        "#           to keep Firecrawl credits in check. Free API portals are\n"
        "#           always read daily whatever the priority.\n\n"
        "companies:\n"
    )
    return header + "\n".join(out) + "\n", len(out)


if __name__ == "__main__":
    text, n = emit()
    import pathlib

    pathlib.Path(__file__).resolve().parent.parent.joinpath("companies.yml").write_text(text)
    print(f"wrote {n} companies")
