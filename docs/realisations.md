# Réalisations de la communauté

Exemples de dashboards créés par les utilisateurs de rtetempo. Ces surcouches d'affichage sont indépendantes de l'intégration : seuls les entity ids les relient au plugin. Merci aux auteurs !

## Mushroom — exemples de Brawdunoir

Contribués via la [PR #48](https://github.com/hekmon/rtetempo/pull/48).

* Couleur du jour et du lendemain ([rendu](../res/mushroom_colors.png), [code](../res/mushroom_colors.yaml))
* Nombre de jours restants sur le cycle ([rendu](../res/mushroom_cycle.png), [code](../res/mushroom_cycle.yaml))
* Les deux combinés ([rendu](../res/mushroom_complete.png), [code](../res/mushroom_complete.yaml))

## Mushroom — version de sleveille4

La couleur des deux icônes s'adapte à la couleur du jour / du lendemain, et l'ensemble n'est visible que s'il reste un jour rouge ou blanc non planifié (visibilité conditionnelle). Rendu dans le [commentaire d'origine](https://github.com/hekmon/rtetempo/issues/47#issuecomment-3131128273).

```yaml
square: false
type: grid
cards:
  - type: custom:mushroom-title-card
    title: EDF Tempo
    alignment: center
    subtitle_tap_action:
      action: none
    title_tap_action:
      action: none
  - square: false
    type: grid
    cards:
      - type: custom:mushroom-template-card
        primary: Aujourd'hui
        secondary: ""
        icon: mdi:home-lightning-bolt
        icon_color: |-
          {% if (states('sensor.rte_tempo_couleur_actuelle') == "Bleu") %}
            blue
          {% elif (states('sensor.rte_tempo_couleur_actuelle') == "Blanc") %}
            white
          {% elif (states('sensor.rte_tempo_couleur_actuelle') == "Rouge") %}
            red
          {% endif %}
        badge_color: ""
        fill_container: true
        layout: vertical
        tap_action:
          action: none
        hold_action:
          action: none
        double_tap_action:
          action: none
      - type: custom:mushroom-template-card
        primary: Demain
        secondary: ""
        icon: mdi:home-lightning-bolt
        icon_color: |-
          {% if (states('sensor.rte_tempo_prochaine_couleur') == "Bleu") %}
            blue
          {% elif (states('sensor.rte_tempo_prochaine_couleur') == "Blanc") %}
            white
          {% elif (states('sensor.rte_tempo_prochaine_couleur') == "Rouge") %}
            red
          {% endif %}
        badge_color: ""
        fill_container: true
        layout: vertical
        tap_action:
          action: none
        hold_action:
          action: none
        double_tap_action:
          action: none
    columns: 2
  - type: custom:mushroom-template-card
    primary: Jours Restants
    secondary: >-
      Bleu: {{states('sensor.rte_tempo_cycle_jours_restants_bleu')}} / Blanc:
      {{states('sensor.rte_tempo_cycle_jours_restants_blanc')}} / Rouge:
      {{states('sensor.rte_tempo_cycle_jours_restants_rouge')}}
    icon: mdi:calendar-multiselect-outline
    icon_color: light-grey
    badge_color: ""
    fill_container: true
    layout: vertical
columns: 1
view_layout:
  position: sidebar
visibility:
  - condition: or
    conditions:
      - condition: numeric_state
        entity: sensor.rte_tempo_cycle_jours_restants_blanc
        above: 0
      - condition: numeric_state
        entity: sensor.rte_tempo_cycle_jours_restants_rouge
        above: 0
```

## Mushroom — version de ChristopheBraud

Gère le basculement de couleur à 6h (« Aujourd'hui, jusqu'à 6h » / « Demain »), la journée Tempo courant de 6h à 6h. Rendu dans le [commentaire d'origine](https://github.com/hekmon/rtetempo/issues/47#issuecomment-3695179238).

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: |-
          {% if now() < today_at("06:00") %}
          Aujourd'hui, jusqu'a 6h
          {%else%}
          Aujourd'hui
          {%endif%}
        secondary: "{{ states(entity) }}"
        icon: mdi:lightning-bolt
        badge_color: ""
        entity: sensor.rte_tempo_couleur_actuelle
        tap_action:
          action: more-info
        color: |-
          {% if is_state(entity, 'Blanc') %}
            grey
          {% elif is_state(entity, 'Bleu') %}
            blue
          {% elif is_state(entity, 'Rouge') %}
            red
          {% else %}
            grey
          {% endif %}
        features_position: bottom
      - type: custom:mushroom-template-card
        primary: |-
          {% if now() < today_at("06:00") %}
          Aujourd'hui, à partir de 6h
          {%else%}
          Demain
          {%endif%}
        secondary: "{{ states(entity) }}"
        icon: mdi:calendar
        icon_color: |-
          {% if is_state(entity, 'Blanc') %}
            grey
          {% elif is_state(entity, 'Bleu') %}
            blue
          {% elif is_state(entity, 'Rouge') %}
            red
          {% else %}
            grey
          {% endif %}
        badge_color: ""
        entity: sensor.rte_tempo_prochaine_couleur
        tap_action:
          action: more-info
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: sensor.rte_tempo_cycle_jours_restants_bleu
        icon_color: blue
        name: Bleu
      - type: custom:mushroom-entity-card
        entity: sensor.rte_tempo_cycle_jours_restants_blanc
        icon_color: grey
        name: Blanc
      - type: custom:mushroom-entity-card
        entity: sensor.rte_tempo_cycle_jours_restants_rouge
        icon_color: red
        name: Rouge
title: Tempo
```
