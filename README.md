# My bpost integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/sdebruyn/homeassistant-bpost-integration/main.svg)](https://results.pre-commit.ci/latest/github/sdebruyn/homeassistant-bpost-integration/main)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/sdebruyn/homeassistant-bpost-integration/Validate/main)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

This is a custom component for [Home Assistant](https://home-assistant.io/)
that allows you to see parcels listed in your bpost Mijn bpost account.

This integration signs in through the same bpost account flow used by
[Mijn bpost](https://www.bpost.be/nl/mijn-bpost).

## Features

Only features with a checked box are available at the moment. Other features are planned for the future.

### Entities

#### Sensor

* [x] The amount of parcels expected for delivery: `sensor.parcels_due`
* [x] A sensor per expected parcel, with tracking details in the attributes
* [x] Public bpost tracking URL, full tracking details, and a compact tracking summary per parcel

#### Binary sensor

* [x] If you're expecting a parcel: `binary_sensor.expecting_parcel`

### Services

* [x] Start tracking a new parcel

## Installation

### Installing the integration as a custom component

This repository is included in the [HACS](https://hacs.xyz) repositories.

### Configure the integration in Home Assistant

1. Go to your Home Assistant settings > Integrations and add a new integration.
2. Search for `bpost` and select it.
3. Enter the email address and password for your bpost account.
   The integration tries to use the postal code from your bpost profile; the optional postal code field is only a fallback.
4. All entities mentioned above are now available.

## Dashboard examples

### Conditional card

Only show parcel details when at least one parcel is expected:

```yaml
type: conditional
conditions:
  - entity: binary_sensor.expecting_parcel
    state: "on"
card:
  type: markdown
  title: bpost parcels
  content: >
    {% macro format_date(value) -%} {{ as_datetime(value).strftime('%a
    %d/%m/%Y') if value and as_datetime(value) else value }} {%- endmacro %}  {%
    set parcels = state_attr('sensor.parcels_due', 'parcels') or [] %} {% if
    parcels | count == 0 %} Geen pakjes verwacht {% else %} **{{
    states('sensor.parcels_due') }} bpost pakje{% if parcels | count > 1 %}s{%
    endif %} verwacht**

    {% for parcel in parcels %} ---

    {% set details = parcel.get('tracking_details') or {} %} {% set summary =
    parcel.get('tracking_summary') or {} %} {% set language =
    (details.get('requestedPreferences') or {}).get('language', 'NL') | upper %}
    {% set language_lower = language | lower %} {% set active_step =
    details.get('activeStep') or {} %} {% set pickup_point =
    details.get('deliveryPoint') or {} %} {% set locker =
    details.get('lockerDetailsDropOff') or {} %} {% set pickup_ready =
    active_step.get('status') == 'active' and 'AVAILABLE' in
    active_step.get('knownProcessStep', '') %}
      
    <details><summary><b>{{ details.get('senderCommercialName') or parcel.get('sender') or parcel.get('tracking_id','Parcel') }}</b>, Status: {{ details.get('activeStep',
    {}).get('label',{}).get('main',{}).get(language,'') }} {{
    details.get('activeStep',
    {}).get('label',{}).get('detail',{}).get(language,'') }}{% if
    parcel.get('expected_delivery') %} , Levering: {{
    parcel.get('expected_delivery') }} {% endif %}, <a href='{{
    parcel.get('tracking_url') }}'>{{ parcel.get('tracking_id', 'Unknown')
    }}</a></summary> {% set events = details.get('events') or
    summary.get('events') or [] %} 

    {% if events %} {% set latest = events[0] %} {% set event_text =
    (latest.get('key') or {}).get(language, {}) %}
      **Laatste update:**{% if
    latest.get('date') %} {{ format_date(latest.get('date')) }}{% if
    latest.get('time') %} at {{ latest.get('time') }}{% endif %}{% elif
    latest.get('timestamp') %} {{
    as_datetime(latest.get('timestamp')).strftime('%d/%m/%Y %H:%M') if
    as_datetime(latest.get('timestamp')) else latest.get('timestamp') }}{% endif
    %}{% if latest.get('location', {}).get('locationName') %}, {{
    latest.get('location', {}).get('locationName') }}{% endif %} — {{
    event_text.get('description') or latest.get('event_description') or
    latest.get('status') or 'Status updated' }} {% endif %}

    {% if pickup_point %} {% set point_type = pickup_point.get('type') or '' %}
    {% set point_name = pickup_point.get('name') or {} %} {% set point_street =
    pickup_point.get('street') or {} %} {% set point_number =
    pickup_point.get('streetNumber') or {} %} {% set point_postcode =
    pickup_point.get('postcode') or {} %} 
      {% set point_city =
    pickup_point.get('municipality') or {} %} **Afhaal punt:** {% if
    pickup_point.get('latitude') and pickup_point.get('longitude') %}
    [{{point_type}}](https://www.google.com/maps/search/?api=1&query={{
    pickup_point.get('latitude') }},{{ pickup_point.get('longitude')
    }}){%else%}{{point_type}}{% endif %} {{
      point_name.get(language_lower) or point_name.get(language) or point_name }}
    {{ point_street.get(language_lower) or point_street.get(language_lower) or
    point_street }} {{ point_number.get(language_lower) or
    point_number.get('en') or point_number }}, {{ point_postcode.get(language |
    lower) or point_postcode.get(language_lower) or point_postcode }} {{
    point_city.get(language_lower) or point_city.get(language_lower) or
    point_city }}


    {% set available_from = details.get('earliestAvailableTime') or {} %} {% set
    available_until = details.get('latestAvailableTime') or {} %} {% if
    available_from.get('day') or available_until.get('day') %} **Ophalen**:{% if
    available_from.get('day') %} van {{ format_date(available_from.get('day'))
    }}{% if available_from.get('time') %} {{ available_from.get('time') }}{%
    endif %}{% endif %}{% if available_until.get('day') %} tot **{{
    format_date(available_until.get('day')) }}{% if available_until.get('time')
    %} {{ available_until.get('time') }}{% endif %}**{% endif %} {% endif %}

    {% set opening_schedules = pickup_point.get('openingSchedules') or [] %} {%
    if pickup_ready and opening_schedules %} {% set day_names = {'MONDAY':
    'Maandag', 'TUESDAY': 'Dinsdag', 'WEDNESDAY': 'Woensdag', 'THURSDAY':
    'Donderdag', 'FRIDAY': 'Vrijdag', 'SATURDAY': 'Zaterdag', 'SUNDAY':
    'Zondag'} %} >**Openingsuren:**<br> {% for schedule in opening_schedules %}
    {{ day_names.get(schedule.get('dayOfTheWeek'), schedule.get('dayOfTheWeek',
    '') | title) }}: {% set hours = schedule.get('openingHours') or [] %}{% if
    hours %}{% for period in hours %}{{ period.get('open') }}–{{
    period.get('close') }}{% if not loop.last %}, {% endif %}{% endfor %}{% else
    %}Gesloten{% endif %}<br> {% endfor %} {% endif %} {% endif %}

      
    **Tracking:** [{{ parcel.get('tracking_id', 'Unknown') }}]({{
    parcel.get('tracking_url') }})

    {% if pickup_ready %} {% set qr_image = locker.get('qrCodeUrl') or
    locker.get('qr_code_url') or details.get('qrCodeUrl') %} {% set locker_code
    = locker.get('qrCode') or locker.get('qr_code') or locker.get('openingCode')
    or details.get('secureDeliveryCode') %} {% if qr_image %} **Scan to open the
    parcel locker**

    ![Locker QR code]({{ qr_image }}) {% elif locker_code %} **Parcel-locker
    access code:** `{{ locker_code }}`  {% endif %} {% endif %}

    **Ontvanger:** {{details.get('receiver',{}).get('name','')}}

      
    **Afmetingen:** {{details.get('dimensionsInCm')}},
    {{((details.get('weightInGrams')| int(0))/1000) | round(2) }}kg {%endfor %}
    </details> {% endif %}
```

### Auto-entities card

If you use the `auto-entities` custom card, you can automatically list the dynamic parcel sensors:

```yaml
type: custom:auto-entities
card:
  type: entities
  title: bpost parcels
filter:
  include:
    - entity_id: sensor.parcel_*
sort:
  method: name
```

If bpost changes the Mijn bpost page payload, the integration may need an
extractor update. Enable debug logging for `custom_components.bpost` when
reporting parcel parsing issues.

## License

MIT license

## Contributing

1. Install [poetry](https://python-poetry.org/)
2. Clone the repository
3. Install dependencies `poetry install`
4. Activate venv: `poetry shell`
5. Configure pre-commit: `pre-commit install`
6. Configure your IDE to use the poetry venv (`poetry env info`)
