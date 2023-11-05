# Fetch historical climate data

Download the following files from: https://worldclim.org/data/worldclim21.html

* `wc2.1_10m_prec.zip`
* `wc2.1_10m_tmax.zip`
* `wc2.1_10m_tmin.zip`
* `wc2.1_10m_vapr.zip`

Create a `data/` directory and unzip the files into that new directory.  The
contents of the `data/` directory should then look like:

```
data/wc2.1_10m_prec_01.tif
data/wc2.1_10m_prec_02.tif
data/wc2.1_10m_prec_03.tif
...
```

# Generate the map

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python convert_src_data_to_image.py
```

Output will be in `monthly_climate_map.png`
