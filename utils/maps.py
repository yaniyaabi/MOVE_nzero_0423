import json
import numpy as np
import urllib.parse

def make_json_safe(x):
    import pandas as pd
    import datetime as dt
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (np.integer,)):  return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (np.bool_,)):    return bool(x)
    if isinstance(x, (dt.datetime, dt.date, dt.time)):
        return x.isoformat()
    if 'pandas' in globals() or 'pd' in globals():
        try:
            if isinstance(x, pd.Timestamp): return x.isoformat()
            if x is getattr(pd, "NaT", object()): return None
        except Exception:
            pass
    if isinstance(x, dict):
        return {k: make_json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [make_json_safe(v) for v in x]
    return str(x)

def normalize_weights(locations, min_size=20, max_size=40):
    if not locations:
        return []
    weights = [loc.get("weight", 0) for loc in locations]
    min_w, max_w = min(weights), max(weights)
    for loc in locations:
        w = loc.get("weight", 0)
        norm = (w - min_w) / (max_w - min_w) if max_w > min_w else 0.5
        scaled = norm * (max_size - min_size) + min_size
        loc["scaled_weight"] = round(float(scaled), 2)
    return locations

def _build_src_with_appkey(pages_url: str, appkey: str) -> str:
    parsed = urllib.parse.urlparse(pages_url)
    qs = urllib.parse.parse_qs(parsed.query)
    qs["appkey"] = [appkey]
    new_query = urllib.parse.urlencode({k: v[0] if isinstance(v, list) else v for k, v in qs.items()})
    return urllib.parse.urlunparse(parsed._replace(query=new_query))

def _iframe_html(PAGES_URL: str, appkey: str, msg_json: str, height: int = 600) -> str:

    src = _build_src_with_appkey(PAGES_URL, appkey)

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Kakao Map</title></head>
<body style="margin:0">
  <iframe id="kmap" src="{src}" style="width:100%;height:{height}px;border:0"></iframe>
  <script>
    (function() {{
      const iframe = document.getElementById('kmap');
      const targetOrigin = new URL("{src}").origin;
      const msg = {msg_json};

      function send() {{
        try {{ iframe.contentWindow.postMessage(msg, targetOrigin); }}
        catch (e) {{ console.error('postMessage 실패:', e); }}
      }}

      // index.html에서 MAP_READY를 보내면 payload 전송
      window.addEventListener('message', (e) => {{
        if (e.origin === targetOrigin && e.data && e.data.type === 'MAP_READY') {{
          send();
        }}
      }});
    }})();
  </script>
</body>
</html>
"""

def default_map_html(PAGES_URL: str, appkey: str, center=(37.207925, 126.824028), level=5, height=700):
    payload = {
        "type": "SET_MARKERS",
        "payload": {
            "center": {"lat": center[0], "lng": center[1]},
            "level": level,
            "locations": []
        }
    }
    return _iframe_html(PAGES_URL, appkey, json.dumps(payload, ensure_ascii=False), height=height)

def markers_map_html(PAGES_URL: str, appkey: str, locations, center=(37.207925, 126.824028), level=5, height=700):
    payload = {
        "type": "SET_MARKERS",
        "payload": {
            "center": {"lat": center[0], "lng": center[1]},
            "level": level,
            "locations": locations
        }
    }
    return _iframe_html(PAGES_URL, appkey, json.dumps(payload, ensure_ascii=False), height=height)

def routes_map_html(PAGES_URL: str, appkey: str, segs, pickups, center=(37.207925, 126.824028), level=5, height=700):
    safe = make_json_safe({
        "type": "SET_ROUTES",
        "payload": {
            "center": {"lat": center[0], "lng": center[1]},
            "level": level,
            "routes": segs,
            "pickups": pickups
        }
    })
    return _iframe_html(PAGES_URL, appkey, json.dumps(safe, ensure_ascii=False), height=height)

def links_map_html(PAGES_URL: str, appkey: str, link_df, height=700, center=(37.207925, 126.824028), level=5):
    max_count = float(link_df["count"].max())
    min_count = float(link_df["count"].min())

    def norm(v, a, b, c, d):
        if b == a: return (c + d) / 2
        t = (v - a) / (b - a)
        return c + t * (d - c)

    links = []
    for _, r in link_df.iterrows():
        c = float(r["count"])
        links.append({
            "start_lat": r["start_lat"], "start_lon": r["start_lon"],
            "end_lat": r["end_lat"],     "end_lon": r["end_lon"],
            "weight": int(norm(c, min_count, max_count, 5, 30)),
            "opacity": float(norm(c, min_count, max_count, 0.5, 1.0)),
            "color": "#002642"
        })
    payload = {"type": "SET_LINKS", "payload": {"links": links, "center": {"lat": center[0], "lng": center[1]}, "level": level}}
    return _iframe_html(PAGES_URL, appkey, json.dumps(payload, ensure_ascii=False), height=height)

def _df_to_features(gdf, value_col):

    import pandas as pd
    from shapely.geometry import Polygon, MultiPolygon

    if not hasattr(gdf, "geometry"):
        raise ValueError("GeoDataFrame - geometry column이 필요")

    vals = pd.to_numeric(gdf[value_col], errors="coerce").fillna(0.0)
    if (vals.max() - vals.min()) > 0:
        norm = (vals - vals.min()) / (vals.max() - vals.min())
    else:
        norm = vals.copy() 

    opacities = (0.15 + 0.75 * norm).clip(0, 0.95)

    features = []
    for (_, row), op in zip(gdf.iterrows(), opacities):
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue

        def poly_to_coords(poly: Polygon):

            ring = list(poly.exterior.coords)
            return [[ [float(x), float(y)] for (x, y) in ring ]]

        if geom.geom_type == "Polygon":
            coords = poly_to_coords(geom)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": coords},
                "properties": {"opacity_value": float(op)}
            })
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                coords = poly_to_coords(poly)
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": coords},
                    "properties": {"opacity_value": float(op)}
                })
        else:
            # 라인/포인트 등은 스킵
            continue
    return features

def polygons_map_html(PAGES_URL: str,
                      appkey: str,
                      gdf,
                      value_col: str,
                      center=(37.219683, 126.818302),
                      level=6,
                      height=700):

    features = _df_to_features(gdf, value_col)
    payload = {
        "type": "SET_GEOJSON",
        "payload": {
            "center": {"lat": center[0], "lng": center[1]},
            "level": level,
            "features": features
        }
    }
    return _iframe_html(PAGES_URL, appkey, json.dumps(payload, ensure_ascii=False), height=height)