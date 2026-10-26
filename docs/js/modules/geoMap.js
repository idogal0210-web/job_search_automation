/**
 * geoMap.js - Lazy-Loaded Interactive Map Controller
 * Initializes Leaflet & Leaflet.markercluster on demand with zero render blocking.
 * Features an extensive Israeli geolocation dictionary and company HQ resolver.
 */

export const ISRAEL_LOCATIONS_GEO = {
  // Tel Aviv & Dan
  'תל אביב': [32.0853, 34.7818],
  'tel aviv': [32.0853, 34.7818],
  'גוש דן': [32.0853, 34.7818],
  'רמת גן': [32.0822, 34.8143],
  'ramat gan': [32.0822, 34.8143],
  'שיבא': [32.0460, 34.8430],
  'תל השומר': [32.0460, 34.8430],
  'גבעתיים': [32.0722, 34.8089],
  'בני ברק': [32.0833, 34.8333],
  'פתח תקווה': [32.0840, 34.8878],
  'petah tikva': [32.0840, 34.8878],
  'פתח תקוה': [32.0840, 34.8878],
  'חולון': [32.0158, 34.7874],
  'holon': [32.0158, 34.7874],
  'בת ים': [32.0194, 34.7500],
  'bat yam': [32.0194, 34.7500],
  'ראשון לציון': [31.9730, 34.7925],
  'rishon': [31.9730, 34.7925],
  'אור יהודה': [32.0294, 34.8572],
  'קריית אונו': [32.0536, 34.8586],
  'יהוד': [32.0333, 34.8833],

  // Center & Shfela & Airport
  'נתב"ג': [32.0005, 34.8707],
  'נתב״ג': [32.0005, 34.8707],
  'לוד': [31.9519, 34.8967],
  'lod': [31.9519, 34.8967],
  'רמלה': [31.9284, 34.8687],
  'ramla': [31.9284, 34.8687],
  'איירפורט סיטי': [32.0120, 34.9220],
  'airport city': [32.0120, 34.9220],
  'נמל תעופה': [32.0005, 34.8707],
  'מודיעין': [31.8986, 35.0104],
  'modiin': [31.8986, 35.0104],
  'שוהם': [31.9986, 34.9458],
  'נס ציונה': [31.9317, 34.7981],
  'נס-ציונה': [31.9317, 34.7981],
  'רחובות': [31.8928, 34.8113],
  'rehovot': [31.8928, 34.8113],
  'יבנה': [31.8781, 34.7397],
  'yavne': [31.8781, 34.7397],
  'שפלה': [31.8928, 34.8113],
  'מרכז': [32.0853, 34.7818],
  'center': [32.0853, 34.7818],
  'מרכז הארץ': [32.0853, 34.7818],

  // Sharon
  'הרצליה': [32.1624, 34.8447],
  'herzliya': [32.1624, 34.8447],
  'רעננה': [32.1848, 34.8713],
  'raanana': [32.1848, 34.8713],
  'כפר סבא': [32.1750, 34.9069],
  'kfar saba': [32.1750, 34.9069],
  'הוד השרון': [32.1528, 34.8878],
  'hod hasharon': [32.1528, 34.8878],
  'נתניה': [32.3215, 34.8532],
  'netanya': [32.3215, 34.8532],
  'פולג': [32.2783, 34.8572],
  'חדרה': [32.4340, 34.9197],
  'hadera': [32.4340, 34.9197],
  'קיסריה': [32.5020, 34.9350],
  'caesarea': [32.5020, 34.9350],
  'עמק חפר': [32.3850, 34.9000],
  'שרון': [32.1848, 34.8713],
  'sharon': [32.1848, 34.8713],

  // South & Ashdod / Ashkelon / Negev
  'אשדוד': [31.8014, 34.6435],
  'ashdod': [31.8014, 34.6435],
  'נמל אשדוד': [31.8260, 34.6530],
  'נמל הדרום': [31.8260, 34.6530],
  'אשקלון': [31.6688, 34.5743],
  'ashkelon': [31.6688, 34.5743],
  'קריית גת': [31.6100, 34.7642],
  'kiryat gat': [31.6100, 34.7642],
  'באר שבע': [31.2529, 34.7915],
  'beer sheva': [31.2529, 34.7915],
  'beersheba': [31.2529, 34.7915],
  'דימונה': [31.0667, 35.0333],
  'dimona': [31.0667, 35.0333],
  'נאות חובב': [31.1350, 34.7890],
  'רמת חובב': [31.1350, 34.7890],
  'ערד': [31.2589, 35.2128],
  'שדרות': [31.5211, 34.5967],
  'קריית מלאכי': [31.7289, 34.7456],
  'אילת': [29.5577, 34.9519],
  'דרום': [31.2529, 34.7915],
  'south': [31.2529, 34.7915],
  'נגב': [31.2529, 34.7915],

  // North & Haifa & Valleys & Galilee
  'חיפה': [32.7940, 34.9896],
  'haifa': [32.7940, 34.9896],
  'מת״ם': [32.7880, 34.9580],
  'מתם': [32.7880, 34.9580],
  'קריות': [32.8300, 35.0700],
  'קריית אתא': [32.8028, 35.1075],
  'קריית ביאליק': [32.8272, 35.0847],
  'קריית מוצקין': [32.8347, 35.0778],
  'קריית ים': [32.8464, 35.0686],
  'נשר': [32.7667, 35.0333],
  'טירת כרמל': [32.7611, 34.9722],
  'עכו': [32.9278, 35.0817],
  'akko': [32.9278, 35.0817],
  'acre': [32.9278, 35.0817],
  'נהריה': [33.0059, 35.0941],
  'nahariya': [33.0059, 35.0941],
  'כרמיאל': [32.9199, 35.2901],
  'karmiel': [32.9199, 35.2901],
  'תפן': [32.9772, 35.2683],
  'יקנעם': [32.6595, 35.1102],
  'yokneam': [32.6595, 35.1102],
  'יקנעם עילית': [32.6595, 35.1102],
  'מגדל העמק': [32.6738, 35.2415],
  'migdal haemek': [32.6738, 35.2415],
  'עפולה': [32.6078, 35.2894],
  'afula': [32.6078, 35.2894],
  'אלון תבור': [32.6517, 35.3524],
  'alon tavor': [32.6517, 35.3524],
  'נצרת': [32.6996, 35.3035],
  'נוף הגליל': [32.7050, 35.3350],
  'ציפורית': [32.7600, 35.3400],
  'טבריה': [32.7922, 35.5312],
  'קריית שמונה': [33.2075, 35.5697],
  'kiryat shmona': [33.2075, 35.5697],
  'קצרין': [32.9917, 35.6900],
  'משגב': [32.8600, 35.2500],
  'צפון': [32.7940, 34.9896],
  'north': [32.7940, 34.9896],
  'גליל': [32.9199, 35.2901],
  'עמקים': [32.6078, 35.2894],

  // Jerusalem & Judea
  'ירושלים': [31.7683, 35.2137],
  'jerusalem': [31.7683, 35.2137],
  'בית שמש': [31.7470, 34.9881],
  'beit shemesh': [31.7470, 34.9881],
  'מעלה אדומים': [31.7917, 35.2972],

  // General Countrywide / Default
  'ישראל': [32.0853, 34.7818],
  'israel': [32.0853, 34.7818],
  'ארצי': [32.0853, 34.7818],
  'היברידי': [32.0853, 34.7818],
  'remote': [32.0853, 34.7818],
  'מרוחק': [32.0853, 34.7818]
};

export const COMPANY_HQ_LOCATIONS_GEO = [
  // Semiconductors & High-Tech Hardware
  [['tower semiconductor', 'טאואר', 'towersemi'], [32.6738, 35.2415], 'מגדל העמק'],
  [['ultra clean', 'uct'], [32.6738, 35.2415], 'מגדל העמק'],
  [['kla', 'קיי אל איי'], [32.6738, 35.2415], 'מגדל העמק'],
  [['applied materials', 'אפלייד מטיריאלס', 'אפלייד'], [31.9077, 34.8080], 'פארק המדע רחובות'],
  [['nova', 'נובה'], [31.9055, 34.8075], 'פארק המדע רחובות'],
  [['stratasys', 'סטראטסיס'], [31.9055, 34.8075], 'פארק המדע רחובות'],
  [['merck', 'מרק'], [31.9055, 34.8075], 'פארק המדע רחובות'],
  [['edwards vacuum', 'edwards', 'אדוורדס'], [31.6100, 34.7642], 'קריית גת'],
  [['intel', 'אינטל'], [31.6100, 34.7642], 'קריית גת'],

  // Energy, Gas, Solar, Utilities & CleanTech
  [['siemens energy', 'סימנס אנרגיה', 'siemens'], [32.0833, 34.9572], 'פארק אפק, ראש העין'],
  [['alumenergy', 'אלומאנרג׳י', 'אלומאנרגי', 'אלומושת'], [32.6517, 35.3524], 'אלון תבור'],
  [['nt-tao', 'compact fusion'], [32.1528, 34.8878], 'הוד השרון'],
  [['solaredge', 'סולאראדג'], [32.1624, 34.8080], 'הרצליה פיתוח'],
  [['enlight', 'אנלייט'], [32.0833, 34.9572], 'ראש העין'],
  [['energix', 'אנרג׳יקס', 'אנרגיקס'], [32.0822, 34.8020], 'בורסת רמת גן'],
  [['doral', 'דוראל'], [32.0822, 34.8050], 'רמת גן'],
  [['ormat', 'אורמת'], [31.8781, 34.7397], 'יבנה'],
  [['jinko', 'ג׳ינקו', 'גינקו'], [32.1624, 34.8447], 'הרצליה'],
  [['solar solutions', 'פתרונות סולאריים'], [32.3850, 34.9000], 'עמק חפר'],
  [['plant supervision'], [32.6517, 35.3524], 'אלון תבור'],
  [['bazan', 'בז״ן', 'בזן', 'בתי זיקוק'], [32.7980, 35.0450], 'מפרץ חיפה'],
  [['paz', 'פז'], [32.2530, 34.8450], 'יקום'],
  [['sonol', 'סונול'], [32.2783, 34.8572], 'פולג, נתניה'],
  [['delek', 'דלק', 'ניו-מד', 'newmed'], [32.1624, 34.8080], 'הרצליה'],
  [['isramco', 'ישראמקו', 'נפטא'], [32.0840, 34.8650], 'פתח תקווה'],

  // Defense, Aerospace, UAVs, Drones & Robotics
  [['elbit', 'אלביט'], [32.7880, 34.9580], 'מת״ם חיפה'],
  [['iai', 'התעשייה האווירית', 'התעשיה האווירית', 'אלתא', 'elta'], [32.0030, 34.8850], 'נתב״ג / לוד'],
  [['rafael', 'רפאל'], [32.8650, 35.0850], 'מכון דוד, קריות'],
  [['controp', 'קונטרופ'], [32.1528, 34.8878], 'הוד השרון'],
  [['assatec', 'אסאטק'], [32.9278, 35.0817], 'עכו / נהריה'],
  [['allpha', 'אלפא אינוביישן'], [32.8120, 35.0340], 'מספנות חיפה'],
  [['bagira', 'בגירה'], [32.0158, 34.7874], 'חולון'],
  [['israel shipyards', 'מספנות ישראל'], [32.8120, 35.0340], 'נמל חיפה'],
  [['airobotics', 'איירובוטיקס'], [32.0910, 34.8650], 'פתח תקווה'],
  [['percepto', 'פרספטו'], [31.8986, 35.0104], 'פארק טכנולוגי מודיעין'],
  [['hevendrones', 'הוונדרונס'], [32.6100, 35.0500], 'פארק מבוא כרמל'],
  [['steadicopter', 'סטדיקופטר'], [32.6738, 35.2415], 'מגדל העמק'],
  [['bluebird', 'בלובריד'], [32.2850, 34.9150], 'קדימה-צורן'],
  [['aeronautics', 'אירונאוטיקס'], [31.8781, 34.7397], 'יבנה'],
  [['copterpix', 'קופטרפיקס'], [31.9986, 34.9458], 'שוהם'],

  // Aviation, Logistics & Transportation
  [['swissport', 'סוויספורט'], [32.0005, 34.8707], 'נתב״ג'],
  [['alstom', 'אלסטום'], [32.0628, 34.7865], 'תל אביב'],
  [['pb', 'parsons brinckerhoff'], [32.0120, 34.9220], 'איירפורט סיטי'],

  // Infrastructure, Water, AgTech & Construction
  [['netafim', 'נטפים'], [32.0715, 34.7930], 'תל אביב'],
  [['nextcom', 'נקסטקום'], [32.6595, 35.1102], 'יקנעם עילית'],
  [['shikun', 'שיכון ובינוי'], [32.0120, 34.9220], 'איירפורט סיטי'],
  [['adama', 'אדמה'], [32.0120, 34.9220], 'איירפורט סיטי'],
  [['danya', 'דניה סיבוס', 'דניה'], [32.0294, 34.8572], 'אור יהודה'],
  [['electra', 'אלקטרה'], [31.9850, 34.7750], 'ראשון לציון'],
  [['ashtrom', 'אשטרום'], [32.0620, 34.7870], 'תל אביב'],
  [['shapir', 'שפיר'], [32.0840, 34.8650], 'פתח תקווה'],
  [['baran', 'ברן'], [32.0020, 34.8290], 'בית דגן'],
  [['icl', 'כי״ל', 'כימיקלים לישראל', 'כיל'], [31.2589, 34.8050], 'באר שבע'],

  // Tech, Telecom, Software, Hospitals & Services
  [['michlol', 'מכלול'], [32.0910, 34.8650], 'פתח תקווה'],
  [['e2e solutions', 'e2e'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
  [['elad', 'אלעד מערכות'], [32.1100, 34.8350], 'רמת החייל, תל אביב'],
  [['sheba', 'שיבא', 'תל השומר'], [32.0460, 34.8430], 'רמת גן'],
  [['mobileye', 'מובילאיי'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
  [['check point', 'checkpoint', "צ'ק פוינט"], [32.0720, 34.7950], 'תל אביב'],
  [['cross river'], [31.8020, 35.2150], 'הר חוצבים, ירושלים'],
  [['jll'], [32.0715, 34.7930], 'תל אביב'],
  [['wix', 'וויקס'], [32.1000, 34.7750], 'נמל תל אביב'],
  [['monday', 'מאנדיי'], [32.0650, 34.7750], 'שדרות רוטשילד, תל אביב'],
  [['fiverr', 'פייבר'], [32.0600, 34.7750], 'תל אביב']
];

export const GENERIC_LOCATION_TERMS = new Set([
  'ישראל', 'israel', 'ארצי', 'היברידי', 'remote', 'מרוחק', 'כל הארץ', 
  'מרכז הארץ', 'מרכז', 'center', 'שרון', 'sharon', 'דרום', 'south', 
  'צפון', 'north', 'שפלה', 'סדנה ויציאה לשטח', 'בשטח'
]);

export function getJobLatLng(job) {
  if (!job) return [32.0853, 34.7818];
  const rawLoc = (job.location || '').toLowerCase();
  const rawComp = (job.company || '').toLowerCase();

  // Deterministic jitter based on job link / ID
  let hash = 0;
  const linkStr = job.link || job.id || (rawComp + rawLoc);
  for (let i = 0; i < linkStr.length; i++) {
    hash = ((hash << 5) - hash) + linkStr.charCodeAt(i);
    hash |= 0;
  }
  const jitterLat = (((Math.abs(hash) % 100) - 50) / 50) * 0.014;
  const jitterLng = (((Math.abs(hash * 31) % 100) - 50) / 50) * 0.014;

  // Step 1: Check specific municipality or industrial site
  for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
    if (!GENERIC_LOCATION_TERMS.has(key) && rawLoc.includes(key)) {
      return [coords[0] + jitterLat, coords[1] + jitterLng];
    }
  }

  // Step 2: Company Headquarters & Main Campus Geo-Mapping
  for (const [keys, coords] of COMPANY_HQ_LOCATIONS_GEO) {
    if (keys.some(k => rawComp.includes(k))) {
      return [coords[0] + jitterLat, coords[1] + jitterLng];
    }
  }

  // Step 3: Regional location matches
  for (const [key, coords] of Object.entries(ISRAEL_LOCATIONS_GEO)) {
    if (rawLoc.includes(key)) {
      return [coords[0] + jitterLat, coords[1] + jitterLng];
    }
  }

  // Step 4: Fallback to Central Israel (Tel Aviv)
  return [32.0853 + jitterLat, 34.7818 + jitterLng];
}

let liveJobsMapInstance = null;
let markersClusterGroup = null;
let leafletLoadingPromise = null;

/**
 * Lazy loads Leaflet CSS & JS and MarkerCluster on demand
 */
export function loadLeafletAssets() {
  if (typeof window !== 'undefined' && typeof window.L !== 'undefined') {
    return Promise.resolve(window.L);
  }
  if (leafletLoadingPromise) return leafletLoadingPromise;

  leafletLoadingPromise = new Promise((resolve, reject) => {
    if (typeof document === 'undefined') {
      return resolve(null);
    }

    // 1. Inject Leaflet CSS
    if (!document.querySelector('link[href*="leaflet"]')) {
      const link1 = document.createElement('link');
      link1.rel = 'stylesheet';
      link1.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      link1.crossOrigin = '';
      document.head.appendChild(link1);

      const link2 = document.createElement('link');
      link2.rel = 'stylesheet';
      link2.href = 'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css';
      document.head.appendChild(link2);

      const link3 = document.createElement('link');
      link3.rel = 'stylesheet';
      link3.href = 'https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css';
      document.head.appendChild(link3);
    }

    // 2. Inject Leaflet JS
    const scriptL = document.createElement('script');
    scriptL.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    scriptL.crossOrigin = '';
    scriptL.onload = () => {
      // 3. Inject MarkerCluster JS
      const scriptMC = document.createElement('script');
      scriptMC.src = 'https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js';
      scriptMC.onload = () => resolve(window.L);
      scriptMC.onerror = () => resolve(window.L);
      document.head.appendChild(scriptMC);
    };
    scriptL.onerror = (err) => reject(err);
    document.head.appendChild(scriptL);
  });

  return leafletLoadingPromise;
}

export function initLiveJobsMap() {
  if (typeof document === 'undefined') return;
  const mapEl = document.getElementById('liveJobsMap');
  if (!mapEl || liveJobsMapInstance) return;

  const L = (typeof window !== 'undefined') ? window.L : null;
  if (!L || typeof L.map !== 'function') {
    // Lazily load Leaflet first then initialize
    loadLeafletAssets().then(() => {
      initLiveJobsMap();
    }).catch(err => {
      console.warn('Could not load Leaflet dynamically:', err);
    });
    return;
  }

  try {
    liveJobsMapInstance = L.map('liveJobsMap', {
      scrollWheelZoom: true,
      zoomControl: true,
      zoomSnap: 0.5,
      zoomDelta: 0.5,
      wheelPxPerZoomLevel: 120,
      wheelDebounceTime: 40,
      zoomAnimation: true,
      zoomAnimationThreshold: 8,
      fadeAnimation: true,
      markerZoomAnimation: true
    }).setView([32.0853, 34.85], 8);

    L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&hl=en', {
      maxZoom: 19,
      keepBuffer: 6,
      updateWhenZooming: false,
      updateWhenIdle: true,
      attribution: '&copy; Google Maps'
    }).addTo(liveJobsMapInstance);

    if (typeof L.markerClusterGroup === 'function') {
      markersClusterGroup = L.markerClusterGroup({
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        maxClusterRadius: 40,
        spiderfyDistanceMultiplier: 1.4,
        iconCreateFunction: function(cluster) {
          const count = cluster.getChildCount();
          let sizeClass = 'small';
          if (count > 25) sizeClass = 'large';
          else if (count > 8) sizeClass = 'medium';
          return L.divIcon({
            html: `<div class="custom-cluster-badge ${sizeClass}"><span>${count}</span></div>`,
            className: 'marker-cluster-custom',
            iconSize: L.point(40, 40)
          });
        }
      });
      liveJobsMapInstance.addLayer(markersClusterGroup);
    } else if (typeof L.layerGroup === 'function') {
      markersClusterGroup = L.layerGroup().addTo(liveJobsMapInstance);
    }

    updateMapMarkers();
  } catch(e) {
    console.error('Error initializing Live Jobs Map:', e);
  }
}

export function updateMapMarkers() {
  if (!liveJobsMapInstance || !markersClusterGroup || typeof window === 'undefined') return;
  const L = window.L;
  if (!L) return;

  markersClusterGroup.clearLayers();

  const visibleCards = document.querySelectorAll('.job-card:not(.is-hidden)');
  const totalVisible = visibleCards.length;
  let mappedCount = 0;
  const latLngBounds = [];

  const allJobsMap = (window.store && window.store.allJobsMap) || window.allJobsMap || {};

  visibleCards.forEach(card => {
    const id = card.getAttribute('data-id');
    const job = allJobsMap[id];
    if (!job) return;

    const [lat, lng] = getJobLatLng(job);
    if (lat && lng) {
      mappedCount++;
      latLngBounds.push([lat, lng]);
    }

    const score = Math.max(0, Math.min(100, Number(job.base_match_score ?? job.match_score) || 0));
    const scoreColor = score >= 85 ? 'var(--dashboard-cyan)' : (score >= 70 ? 'var(--dashboard-lime)' : 'var(--dashboard-gold)');
    const scoreBorder = score >= 85 ? 'rgba(137, 244, 231, 0.8)' : (score >= 70 ? 'rgba(220, 255, 114, 0.8)' : 'rgba(255, 211, 104, 0.8)');

    const companyName = job.company || 'חברה';
    const title = job.title || 'משרה';
    const safeComp = String(companyName).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeTitle = String(title).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeId = encodeURIComponent(id).replace(/'/g, '%27');

    const customIcon = L.divIcon({
      className: 'custom-map-marker',
      html: `
        <div class="custom-map-marker-inner" title="${safeComp} - ${safeTitle}">
          <div class="map-pin-logo-bubble" style="border-color: ${scoreBorder};">
            <span class="map-pin-score-badge" style="background: ${scoreColor}; color: #0f172a;">${score}%</span>
            <div class="map-pin-avatar-fallback">${safeComp.slice(0, 2)}</div>
          </div>
          <div class="map-pin-pointer" style="border-top-color: ${scoreBorder};"></div>
          <div class="map-pin-company-name" dir="auto">${safeComp}</div>
        </div>
      `,
      iconSize: [96, 70],
      iconAnchor: [48, 45],
      popupAnchor: [0, -45]
    });

    const marker = L.marker([lat, lng], { icon: customIcon });

    const popupHtml = `
      <div style="direction: rtl; text-align: right; min-width: 220px; max-width: 280px; font-family: 'Assistant', sans-serif;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
          <div style="flex: 1; min-width: 0;">
            <div style="font-size: 11px; color: var(--dashboard-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" dir="auto"><bdi>${safeComp}</bdi></div>
            <div style="font-size: 13px; font-weight: 700; color: #fff; line-height: 1.25;" dir="auto"><bdi>${safeTitle}</bdi></div>
          </div>
        </div>
        <div style="font-size: 11.5px; color: var(--dashboard-muted); display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px;">
          <span>${job.location || 'ישראל'}</span>
          <span style="color: ${scoreColor}; font-weight: 700;">התאמה ${score}%</span>
        </div>
        <div style="display: flex; gap: 8px; margin-top: 4px;">
          <button onclick="openJobModal(decodeURIComponent('${safeId}'))" class="btn-triage" style="flex: 1; min-height: 32px; padding: 4px 8px; font-size: 12px; cursor: pointer; border-radius: 999px;">
            צפה בכרטיס
          </button>
        </div>
      </div>
    `;

    marker.bindPopup(popupHtml, {
      maxWidth: 300,
      className: 'glass-leaflet-popup'
    });

    marker.addTo(markersClusterGroup);
  });

  const markerCountEl = document.getElementById('mapMarkersCountText');
  if (markerCountEl) {
    if (mappedCount === 0) {
      markerCountEl.textContent = 'אין משרות להצגה על המפה';
    } else {
      markerCountEl.textContent = `מוצגות ${mappedCount} מתוך ${totalVisible} משרות על המפה`;
    }
  }

  if (latLngBounds.length > 0 && typeof L.latLngBounds === 'function') {
    try {
      const bounds = L.latLngBounds(latLngBounds);
      liveJobsMapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    } catch(e) {}
  }
}

// Window export for tests and backwards compatibility
if (typeof window !== 'undefined') {
  window.ISRAEL_LOCATIONS_GEO = ISRAEL_LOCATIONS_GEO;
  window.COMPANY_HQ_LOCATIONS_GEO = COMPANY_HQ_LOCATIONS_GEO;
  window.getJobLatLng = getJobLatLng;
  window.initLiveJobsMap = initLiveJobsMap;
  window.updateMapMarkers = updateMapMarkers;
  window.loadLeafletAssets = loadLeafletAssets;
}
