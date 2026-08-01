# Blueprint — Genesis EventBus

## Objetivo

Permitir comunicação desacoplada entre componentes do Gênesis.

## Responsabilidades

- registrar listeners por tipo de evento;
- publicar eventos;
- executar todos os listeners registrados;
- impedir que a falha de um listener interrompa os demais;
- registrar erros por meio do Logger.

## Componentes existentes

- `Core/events.py`
- `Core/event_bus.py`
- `Core/dispatcher.py`
- `Core/logger.py`

## Fluxo

Evento

↓

EventBus

↓

Dispatcher

↓

Listeners

## Interface pública

```python
event_bus.subscribe(event_type, callback)
event_bus.publish(event)
