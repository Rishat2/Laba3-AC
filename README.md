# Stack Machine. Транслятор и модель

- Валиев Ришат Ильшатович, P3233
- asm | stack | neum | hw | instr | struct | stream | mem | pstr | prob1 
- Упрощенный вариант

## Язык программирования

Синтаксис в расширенной БНВ.

- `[ ... ]` -- вхождение 0 или 1 раз
- `{ ... }` -- вхождение 0 или несколько раз
- `{ ... }-` -- вхождение 1 или несколько раз

```ebnf
program ::= section_data "\n" section_text

section_data ::= "section .data:" [ comment ] "\n" { data_line }

data_line ::= variable comment

variable ::= variable_name ":" variable_value

variable_name ::= <any of "a-z A-Z _"> { <any of "a-z A-Z 0-9 _"> }

variable_value ::= integer
                 | string
                 | buffer
                 | variable_name
                 
section_text ::= "section .text:" [ comment ] "\n" { command_line }

command_line ::= label comment 
               | command comment

label ::= <any of "a-z A-Z _"> { <any of "a-z A-Z 0-9 _"> }

command ::= op0 comment
          | op1 comment
          
op0 ::= add
      | sub
      | mul
      | div
      | mod
      | inc
      | dec
      | dup
      | over
      | switch
      | cmp
      | ret
      | push
      | pop
      | drop
      | halt
      
op1 ::= jmp label
      | jz label
      | jnz label
      | call label
      | lit integer
      | lit variable
      | lit in
      | lit out
                
integer ::= [ "-" ] { <any of "0-9"> }-

positive_integer ::= <any of "1-9"> { <any of "0-9"> }

string ::= "\"" { <any symbol except "\t \n"> } "\""
         | "\'" { <any symbol except "\t \n"> } "\'"

buffer ::= "bf " positive_integer

comment ::= ";" { <any symbol except "\n"> }
```

Команды:

- `add` -- сумма двух значений на верхушке стека данных кладется на верхушку
  стека данных `[a, b] -> [b + a]`
- `sub` -- разность двух значений на верхушке стека данных (из первого вычитается второе)
  кладется на верхушку стека данных `[a, b] -> [b - a]`
- `mul` -- произведение двух значений на верхушке стека данных кладется на верхушку стека данных `[a, b] -> [b * a]`
- `div` -- целочисленное деление двух значений на верхушке стека данных
  (первое делится на второе) кладется на верхушку стека данных `[a, b] -> [b / a]`
- `mod` -- остаток от деления двух значений на верхушке стека данных (первое делится на второе)
  кладется на верхушку стека данных `[a, b] -> [b % a]`
- `inc` -- вместо значения на верхушке стека данных положить данное значение, увеличенное на единицу `[a] -> [a + 1]`
- `dec` -- вместо значения на верхушке стека данных положить данное значение, уменьшенное на единицу `[a] -> [a - 1]`
- `dup` -- продублировать на верхушку стека данных текущее значение на верхушке стека данных `[a] -> [a, a]`
- `over` -- положить на верхушку стека данных следующее значение после текущей верхушки стека данных
  `[a, b] -> [a, b, a]`
- `switch` -- поменять верхушку стека данных и следующее значение местами `[a, b] -> [b, a]`
- `cmp` -- установить флаги результата операции `sub` (стек данных не меняется) `[a, b] -> [a, b] + updated_flags`
- `jmp label` -- переход на указанную метку
- `jz label` -- переход на указанную метку при условии, что `z-flag` равен 1,
  иначе - переход к следующей по порядку команде
- `jnz label` -- переход на указанную метку при условии, что `z-flag` равен 0,
  иначе - переход к следующей по порядку команде
- `call label` -- вызов подпрограммы по указанной метке
- `ret` -- возврат из вызванной подпрограммы при помощи команды `call`
- `lit integer` -- положить на верхушку стека данных переданное целочисленное значение
- `lit variable` -- положить на верхушку стека данных адрес, с которого начинается переданная переменная
- `push` -- взять адрес с верхушки стека данных и положить вместо него значение из памяти по указанному адресу
  `[address] -> [value_from_memory]`
- `pop` -- взять адрес с верхушки стека данных и записать в память следующее значение после верхушки стека данных
  `[value, address] -> []`
- `drop` -- удалить значение с верхушки стека данных `[a] -> []`
- `halt` -- останов

## Организация памяти

- Память соответствует фон Неймановской архитектуре.
- Размер машинного слова неограничен.
- Адресация - абсолютная.

```text
           memory
+----------------------------+
| 00 : start address (n)     |
| 01 : input port            |
| 02 : output port           |
| 03 :      ...              | 
|    part for variables      |
|           ...              |
| n  : program start         |
|           ...              |
+----------------------------+
```

- Ячейка памяти `0` соответствует адресу первой инструкции (началу кода, написанного в секции .text).
- Ячейки памяти `1` и `2` соответствуют `memory-mapped портам ввода-вывода`.
- С ячейки памяти `3` начинается секция `.data`. Переменные могут быть четырех типов:
    - `Целочисленные` -- под них отводится одна ячейка памяти;
    - `Строковые` -- под них отводится `n + 1` последовательных ячеек памяти, где `n` - длина строки
      (дополнительный символ - `нуль-терминатор`);
    - `Буфферные` -- под них отводится `n` последовательных ячеек памяти, где `n` - значение из запроса на выделение
      памяти (`bf n`);
    - `Ссылочные` -- это `целочисленные` переменные, но при начальной инициализации хранят адрес другой переменной.
      Под них отводится одна ячейка памяти.

  Переменные располагаются в памяти в таком порядке, в котором они указаны в исходном коде в секции `.data`.
- С ячейки памяти `n` начинаются инструкции, соответствующие исходному коду, прописанному в секции `.text`.

## Система команд

Особенности процессора:

- Доступ к памяти осуществляется по адресу, хранящемуся в специальном регистре `PC (programm counter)`.
  Установка адреса осуществляется тремя разными способами:
    - Путем инкрементирования текущего значения, записанного в `PC`;
    - Путем записи значения с верхушки `стека адресов`;
    - Путем записи значения с верхушки `стека данных`.
- Поток управления:
    - увеличение `PC` на `1` после каждой команды
    - условный (`jz` или `jnz`) и безусловный (`jmp`) переходы

### Набор инструкций

Команды языка однозначно транслируюстя в инструкции (см. описание в разделе `Язык программирования`)

| Инструкция | Кол-во тактов |
|:-----------|---------------|
| add        | 4             |
| sub        | 4             |
| mul        | 4             |
| div        | 4             |
| mod        | 4             |
| inc        | 3             |
| dec        | 3             |
| dup        | 3             |
| over       | 5             |
| switch     | 4             |
| cmp        | 4             |
| jmp        | 2             |
| jz         | 1             |
| jnz        | 1             |
| call       | 4             |
| ret        | 2             |
| lit        | 2             |
| push       | 4             |
| pop        | 5             |
| drop       | 1             |

Стоит учитывать, что в таблице приведено кол-во тактов на `цикл исполнения` инструкции.
`Цикл выборки` следующей инструкции выполняется за `2` такта.

### Кодирование инструкций

Инструкции имеют представление в виде словарей и состоят из опкода и операнда, инструкции идут последовательно без пропусков
(соответствие между инструкцией и ее опкодом можно прочитать в файле `isa.py` в классе `Opcode`).

## Транслятор

Интерфейс командной строки: `python3 translator.py <source_file> <target_file>`

Реализовано в модуле: [translator](./translator.py)

Этапы трансляции (функция `translate_source`):

1. Очистка исходного текста от пустых строк, лишних пробелов и комментариев (функция `clean`).
2. Выделение переменных (функция `translate_section_data`).
3. Выделение меток и команд (функция `translate_section_text`).
4. Трансляция переменных в машинный код (функция `translate_variables`).
5. Трансляция команд в машинный код (функция `translate_commands`).
6. Объединение результатов двух последних шагов и формирование машинного кода.

Правила трансляции:

- Одна переменная - одна ячейка массива.
- Одна команда - одна ячейка массива.
- Метки пишутся в отдельной строке.
- Названия секций пишутся в отдельной строке.
- Ссылаться можно только на существующие переменные и метки.

## Модель процессора

Интерфейс командной строки: `python3 machine.py <binary_code_file> <input_file>`

Реализовано в модуле: [machine](./machine.py)

### DataPath

```text
                                                                       
                        +---------+                 +---------+          
                 wr_ds->|  data   |                 | address |<-wr_ds
                 re_ds->|  stack  |                 |  stack  |<-re_ds
                        |         |                 |         |
                  value +---------+ op_2    pc_value+---------+ pc_value
           +----------->|  tds    |---+       +-----|  tas    |<-------------+          
           |            +---------+   |       |     +---------+              |
           |             op_1|        v       |                              |
        +-----+              |       +-----+  |                              |
        | mux |<-sel         |  sel->| mux |  |                              |
        +-----+              |       +-----+  |                              |
          ^  ^               |         |      |   +----------(+1)------------+
          |  |               v         v      |   |                          |
          |  | +1-1+-*/%~  _______  _______   |   |   +---+                  |
          |  | ----------->\      \/      /   |   +-->| m |      +--------+  |  
          |  |        z_flag\    alu     /    +------>| u |----->|   pc   |--+
        +-|--|---------------\__________/     +------>| x |      +--------+  |
        | |  |                    |           |       +---+         ^        |
        | |  +--------------------+-----------+         ^           |        |
        | +----------------+                  |         |        latch_pc    |
        |                  |           data_in|        sel                   |
        v                  |                  v                              |
+---------+                |       +--------------+                          |
| control |                |       |              |                          |
|  unit   |<---------------+-------| memory + I/O |<-------------------------+
+---------+ instr          data_out|              | address
                                   +--------------+
                                       ^      ^ 
                                       |      |
                                     wr_mem re_mem
```

Реализован в классе `DataPath`.

`data_stack` -- стек данных. Схема с более детальным описанием модуля `TDS (top of data stack)`:

```text
                           +---------+
                    wr_ds->|  data   |
                    re_ds->|  stack  |
                           |         |
                           +---------+
                               ^ | data_out
                        data_in| |
                               | |            tods
           +--------------------------------------------------------------------------|
           |                   | |                                                    |
           |     +---------------+-------------------------+                          |
           |     |             |                           |                          |
           |     |  +---+      |                           v                          |
           |     +->| m |   +----------+                 +----------+                 |
    value  |        | u |-->| tds_1    |<-latch_tds_1    | tds_2    |<-latch_tds_2    |
    -------|------->| x |   +----------+                 +----------+                 |
           |        +---+      |                       |                              |
           |          ^        |                       |                              |
           |          |        |                       |                              |
           |         sel       |                       |                              |
           +--------------------------------------------------------------------------+
                               |                       |
                               | op_1                  | op_2
                               v                       v 
```

`tds_1` и `tds_2` -- регистры для ввода/вывода стека данных.

`address_stack` -- стек адресов. Схема с более детальным описанием модуля `tas (top of address stack)`:

```text
                +---------+
                | address |<-wr_as
                |  stack  |<-re_as
                |         |
                +---------+
                  ^    |data_out
           data_in|    |
                  |    |            toas
            +---------------------------------+
            |     |    |                      |
            |     |    +----------------+     |
            |     |                     |     |
    pc_value|    +--------+    +---+    |     |
   <--------|----| tas    |<---| m |<---+     |
            |    +--------+    | u |          | pc_value
            |       ^          | x |<---------|---------
            |       |          +---+          |
            |   latch_tas        ^            |
            |                    |            |
            |                   sel           |
            +---------------------------------+
```

`tas` -- регистр для ввода/вывода стека адрессов.

Сигналы (обрабатываются за один такт, реализованы в качестве методов класса):

- `wr_ds` -- запись в стек данных, на верхушку записывается значение из tods_1;
- `re_ds` -- чтение из стека данных, значение с верхушки записывается в один или во все регистры tods
  (зависит от сигналов `latch_tds_1`, `latch_tds_2`);
- `latch_tds_1`, `latch_tds_2` -- защелкнуть входное значение в регистр `tds_1`, `tds_2`, соответственно;
- `wr_as` -- запись в стек адрессов, на верхушку записывается значение из toas;
- `re_as` -- чтение из стека адрессов, значение с верхушки записывается в `toas`;
- `latch_tas` -- защелкнуть входное значение в регистр `tas`;
- `+1` -- сигнал `alu` выполнить операцию инкремента;
- `-1` -- сигнал `alu` выполнить операцию декремента;
- `+` -- сигнал `alu` выполнить операцию сложения;
- `-` -- сигнал `alu` выполнить операцию вычитания;
- `*` -- сигнал `alu` выполнить операцию умножения;
- `/` -- сигнал `alu` выполнить операцию целочисленного деления;
- `%` -- сигнал `alu` выполнить операцию взятия остатка от деления;
- `~` -- сигнал `alu` выполнить операцию сравнения;
- `latch_pc` -- защелкнуть входное значение в регистр `pc`;
- `wr_mem` -- запись в память по переданному адресу;
- `re_mem` -- чтение из памяти по переданному адресу.

Флаги:

- `z_flag` -- отражает нулевое значение результата операции в `alu`;

### ControlUnit

```text
                                    +------+
                              +---->| tick |
                              |     +------+
                              |         |
                    +-------------+     |
                    | instruction |<----+
                    |   decoder   |
                    +-------------+     
                      ^       ^  |
                 instr| z_flag|  | signals
                      |       |  v
                    +---------------+
                    |   data path   |
                    |               |
                    +---------------+
```

Реализовано в классе `ControlUnit`.

- Hardwired (реализовано полностью на Python).
- Выполняет предварительную инициализацию машины -- выполняет список инструкций, чтобы защелкнуть адрес первой
  инструкции в `pc` (метод `initialization`).
- Выполнение и декодирование инструкций происходит в методе `decode_and_execute_instruction`.
- `tick` нужен для подсчета тактов (пригождается при вызове прерываний).

Особенности работы модели:

- Цикл симуляции осуществляется в функции `simulation`.
- Шаг моделирования соответствует одной инструкции с выводом состояния в журнал.
- Для журнала состояний процессора используется стандартный модуль `logging`.
- Количество инструкций для моделирования лимитировано.
- Остановка моделирования осуществляется при:
    - превышении лимита количества выполняемых инструкций;
    - исключении `StopIteration` -- если выполнена инструкция `halt`.

## Тестирование

- Тестирование осуществляется при помощи golden test-ов.
- Настройка golden тестирования находится в [файле](./golden_test.py)
- Конфигурация golden test-ов лежит в [директории](./golden)

Запустить тесты: `poetry run pytest . -v`

Обновить конфигурацию golden tests:  `poetry run pytest . -v --update-goldens`

CI при помощи Github Actions:

```yaml
name: Stack-Machine

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python3 -m pip install --upgrade pip
          pip3 install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python3 -m pip install --upgrade pip
          pip3 install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

- `poetry` -- управления зависимостями для языка программирования Python.
- `coverage` -- формирование отчёта об уровне покрытия исходного кода.
- `pytest` -- утилита для запуска тестов.
- `ruff` -- утилита для форматирования и проверки стиля кодирования.

Пример использования и журнал работы процессора на примере `add`:

```shell
(laba3-ac-py3.10) PS C:\Laba3-AC> python .\translator.py .\examples\cat target
source LoC: 24 code instr: 23
(laba3-ac-py3.10) PS C:\Laba3-AC> python .\machine.py target .\examples\input
DEBUG:root:TICK: 6          PC: 5          TDS1: 1          TDS2: 0          TAS: 0          Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:TICK: 12         PC: 6          TDS1: 6          TDS2: 0          TAS: 6          Z_FLAG: 0       push
         DATA_STACK: [6]
         ADDRESS_STACK: []
DEBUG:root:TICK: 16         PC: 7          TDS1: 3          TDS2: 0          TAS: 6          Z_FLAG: 0       lit 3
         DATA_STACK: [6, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 23         PC: 8          TDS1: 3          TDS2: 6          TAS: 8          Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 27         PC: 9          TDS1: 3          TDS2: 6          TAS: 8          Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 33         PC: 10         TDS1: 6          TDS2: 6          TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [6]
         ADDRESS_STACK: []
DEBUG:root:TICK: 37         PC: 11         TDS1: 0          TDS2: 6          TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [6, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 43         PC: 12         TDS1: 0          TDS2: 6          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [6, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 45         PC: 13         TDS1: 0          TDS2: 6          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [6, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 48         PC: 14         TDS1: 0          TDS2: 6          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [6]
         ADDRESS_STACK: []
DEBUG:root:TICK: 53         PC: 15         TDS1: 5          TDS2: 6          TAS: 10         Z_FLAG: 0       dec
         DATA_STACK: [5]
         ADDRESS_STACK: []
DEBUG:root:TICK: 57         PC: 16         TDS1: 3          TDS2: 6          TAS: 10         Z_FLAG: 0       lit 3
         DATA_STACK: [5, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 64         PC: 17         TDS1: 3          TDS2: 5          TAS: 17         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 68         PC: 18         TDS1: 1          TDS2: 5          TAS: 17         Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 'R'
DEBUG:root:TICK: 74         PC: 19         TDS1: 82         TDS2: 5          TAS: 19         Z_FLAG: 0       push
         DATA_STACK: [82]
         ADDRESS_STACK: []
DEBUG:root:TICK: 78         PC: 20         TDS1: 2          TDS2: 5          TAS: 19         Z_FLAG: 0       lit 2
         DATA_STACK: [82, 2]
         ADDRESS_STACK: []
DEBUG:root:output: '' << 'R'
DEBUG:root:TICK: 85         PC: 21         TDS1: 2          TDS2: 82         TAS: 21         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 89         PC: 8          TDS1: 8          TDS2: 82         TAS: 21         Z_FLAG: 0       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 93         PC: 9          TDS1: 3          TDS2: 82         TAS: 21         Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 99         PC: 10         TDS1: 5          TDS2: 82         TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [5]
         ADDRESS_STACK: []
DEBUG:root:TICK: 103        PC: 11         TDS1: 0          TDS2: 82         TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [5, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 109        PC: 12         TDS1: 0          TDS2: 5          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [5, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 111        PC: 13         TDS1: 0          TDS2: 5          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [5, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 114        PC: 14         TDS1: 0          TDS2: 5          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [5]
         ADDRESS_STACK: []
DEBUG:root:TICK: 119        PC: 15         TDS1: 4          TDS2: 5          TAS: 10         Z_FLAG: 0       dec
         DATA_STACK: [4]
         ADDRESS_STACK: []
DEBUG:root:TICK: 123        PC: 16         TDS1: 3          TDS2: 5          TAS: 10         Z_FLAG: 0       lit 3
         DATA_STACK: [4, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 130        PC: 17         TDS1: 3          TDS2: 4          TAS: 17         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 134        PC: 18         TDS1: 1          TDS2: 4          TAS: 17         Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 'i'
DEBUG:root:TICK: 140        PC: 19         TDS1: 105        TDS2: 4          TAS: 19         Z_FLAG: 0       push
         DATA_STACK: [105]
         ADDRESS_STACK: []
DEBUG:root:TICK: 144        PC: 20         TDS1: 2          TDS2: 4          TAS: 19         Z_FLAG: 0       lit 2
         DATA_STACK: [105, 2]
         ADDRESS_STACK: []
DEBUG:root:output: 'R' << 'i'
DEBUG:root:TICK: 151        PC: 21         TDS1: 2          TDS2: 105        TAS: 21         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 155        PC: 8          TDS1: 8          TDS2: 105        TAS: 21         Z_FLAG: 0       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 159        PC: 9          TDS1: 3          TDS2: 105        TAS: 21         Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 165        PC: 10         TDS1: 4          TDS2: 105        TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [4]
         ADDRESS_STACK: []
DEBUG:root:TICK: 169        PC: 11         TDS1: 0          TDS2: 105        TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [4, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 175        PC: 12         TDS1: 0          TDS2: 4          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [4, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 177        PC: 13         TDS1: 0          TDS2: 4          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [4, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 180        PC: 14         TDS1: 0          TDS2: 4          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [4]
         ADDRESS_STACK: []
DEBUG:root:TICK: 185        PC: 15         TDS1: 3          TDS2: 4          TAS: 10         Z_FLAG: 0       dec
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 189        PC: 16         TDS1: 3          TDS2: 4          TAS: 10         Z_FLAG: 0       lit 3
         DATA_STACK: [3, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 196        PC: 17         TDS1: 3          TDS2: 3          TAS: 17         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 200        PC: 18         TDS1: 1          TDS2: 3          TAS: 17         Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 's'
DEBUG:root:TICK: 206        PC: 19         TDS1: 115        TDS2: 3          TAS: 19         Z_FLAG: 0       push
         DATA_STACK: [115]
         ADDRESS_STACK: []
DEBUG:root:TICK: 210        PC: 20         TDS1: 2          TDS2: 3          TAS: 19         Z_FLAG: 0       lit 2
         DATA_STACK: [115, 2]
         ADDRESS_STACK: []
DEBUG:root:output: 'Ri' << 's'
DEBUG:root:TICK: 217        PC: 21         TDS1: 2          TDS2: 115        TAS: 21         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 221        PC: 8          TDS1: 8          TDS2: 115        TAS: 21         Z_FLAG: 0       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 225        PC: 9          TDS1: 3          TDS2: 115        TAS: 21         Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 231        PC: 10         TDS1: 3          TDS2: 115        TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 235        PC: 11         TDS1: 0          TDS2: 115        TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [3, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 241        PC: 12         TDS1: 0          TDS2: 3          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [3, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 243        PC: 13         TDS1: 0          TDS2: 3          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [3, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 246        PC: 14         TDS1: 0          TDS2: 3          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 251        PC: 15         TDS1: 2          TDS2: 3          TAS: 10         Z_FLAG: 0       dec
         DATA_STACK: [2]
         ADDRESS_STACK: []
DEBUG:root:TICK: 255        PC: 16         TDS1: 3          TDS2: 3          TAS: 10         Z_FLAG: 0       lit 3
         DATA_STACK: [2, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 262        PC: 17         TDS1: 3          TDS2: 2          TAS: 17         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 266        PC: 18         TDS1: 1          TDS2: 2          TAS: 17         Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 'h'
DEBUG:root:TICK: 272        PC: 19         TDS1: 104        TDS2: 2          TAS: 19         Z_FLAG: 0       push
         DATA_STACK: [104]
         ADDRESS_STACK: []
DEBUG:root:TICK: 276        PC: 20         TDS1: 2          TDS2: 2          TAS: 19         Z_FLAG: 0       lit 2
         DATA_STACK: [104, 2]
         ADDRESS_STACK: []
DEBUG:root:output: 'Ris' << 'h'
DEBUG:root:TICK: 283        PC: 21         TDS1: 2          TDS2: 104        TAS: 21         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 287        PC: 8          TDS1: 8          TDS2: 104        TAS: 21         Z_FLAG: 0       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 291        PC: 9          TDS1: 3          TDS2: 104        TAS: 21         Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 297        PC: 10         TDS1: 2          TDS2: 104        TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [2]
         ADDRESS_STACK: []
DEBUG:root:TICK: 301        PC: 11         TDS1: 0          TDS2: 104        TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [2, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 307        PC: 12         TDS1: 0          TDS2: 2          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [2, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 309        PC: 13         TDS1: 0          TDS2: 2          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [2, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 312        PC: 14         TDS1: 0          TDS2: 2          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [2]
         ADDRESS_STACK: []
DEBUG:root:TICK: 317        PC: 15         TDS1: 1          TDS2: 2          TAS: 10         Z_FLAG: 0       dec
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:TICK: 321        PC: 16         TDS1: 3          TDS2: 2          TAS: 10         Z_FLAG: 0       lit 3
         DATA_STACK: [1, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 328        PC: 17         TDS1: 3          TDS2: 1          TAS: 17         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 332        PC: 18         TDS1: 1          TDS2: 1          TAS: 17         Z_FLAG: 0       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 'a'
DEBUG:root:TICK: 338        PC: 19         TDS1: 97         TDS2: 1          TAS: 19         Z_FLAG: 0       push
         DATA_STACK: [97]
         ADDRESS_STACK: []
DEBUG:root:TICK: 342        PC: 20         TDS1: 2          TDS2: 1          TAS: 19         Z_FLAG: 0       lit 2
         DATA_STACK: [97, 2]
         ADDRESS_STACK: []
DEBUG:root:output: 'Rish' << 'a'
DEBUG:root:TICK: 349        PC: 21         TDS1: 2          TDS2: 97         TAS: 21         Z_FLAG: 0       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 353        PC: 8          TDS1: 8          TDS2: 97         TAS: 21         Z_FLAG: 0       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 357        PC: 9          TDS1: 3          TDS2: 97         TAS: 21         Z_FLAG: 0       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 363        PC: 10         TDS1: 1          TDS2: 97         TAS: 10         Z_FLAG: 0       push
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:TICK: 367        PC: 11         TDS1: 0          TDS2: 97         TAS: 10         Z_FLAG: 0       lit 0
         DATA_STACK: [1, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 373        PC: 12         TDS1: 0          TDS2: 1          TAS: 10         Z_FLAG: 0       cmp
         DATA_STACK: [1, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 375        PC: 13         TDS1: 0          TDS2: 1          TAS: 10         Z_FLAG: 0       jz 22
         DATA_STACK: [1, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 378        PC: 14         TDS1: 0          TDS2: 1          TAS: 10         Z_FLAG: 0       drop
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:TICK: 383        PC: 15         TDS1: 0          TDS2: 1          TAS: 10         Z_FLAG: 1       dec
         DATA_STACK: [0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 387        PC: 16         TDS1: 3          TDS2: 1          TAS: 10         Z_FLAG: 1       lit 3
         DATA_STACK: [0, 3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 394        PC: 17         TDS1: 3          TDS2: 0          TAS: 17         Z_FLAG: 1       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 398        PC: 18         TDS1: 1          TDS2: 0          TAS: 17         Z_FLAG: 1       lit 1
         DATA_STACK: [1]
         ADDRESS_STACK: []
DEBUG:root:input: 't'
DEBUG:root:TICK: 404        PC: 19         TDS1: 116        TDS2: 0          TAS: 19         Z_FLAG: 1       push
         DATA_STACK: [116]
         ADDRESS_STACK: []
DEBUG:root:TICK: 408        PC: 20         TDS1: 2          TDS2: 0          TAS: 19         Z_FLAG: 1       lit 2
         DATA_STACK: [116, 2]
         ADDRESS_STACK: []
DEBUG:root:output: 'Risha' << 't'
DEBUG:root:TICK: 415        PC: 21         TDS1: 2          TDS2: 116        TAS: 21         Z_FLAG: 1       pop
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 419        PC: 8          TDS1: 8          TDS2: 116        TAS: 21         Z_FLAG: 1       jmp 8
         DATA_STACK: []
         ADDRESS_STACK: []
DEBUG:root:TICK: 423        PC: 9          TDS1: 3          TDS2: 116        TAS: 21         Z_FLAG: 1       lit 3
         DATA_STACK: [3]
         ADDRESS_STACK: []
DEBUG:root:TICK: 429        PC: 10         TDS1: 0          TDS2: 116        TAS: 10         Z_FLAG: 1       push
         DATA_STACK: [0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 433        PC: 11         TDS1: 0          TDS2: 116        TAS: 10         Z_FLAG: 1       lit 0
         DATA_STACK: [0, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 439        PC: 12         TDS1: 0          TDS2: 0          TAS: 10         Z_FLAG: 1       cmp
         DATA_STACK: [0, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 443        PC: 22         TDS1: 22         TDS2: 0          TAS: 10         Z_FLAG: 1       jz 22
         DATA_STACK: [0, 0]
         ADDRESS_STACK: []
DEBUG:root:TICK: 445        PC: 23         TDS1: 22         TDS2: 0          TAS: 10         Z_FLAG: 1       halt
         DATA_STACK: [0, 0]
         ADDRESS_STACK: []
Rishat

instr_counter: 93 ticks: 445

```

Пример проверки исходного кода:

```shell
(laba3-ac-py3.10) PS C:\Laba3-AC> poetry run pytest . -v 
=============================================================================== test session starts ===============================================================================
platform win32 -- Python 3.10.7, pytest-7.4.4, pluggy-1.5.0 -- C:\Users\basab\AppData\Local\pypoetry\Cache\virtualenvs\laba3-ac-r67BILjG-py3.10\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Laba3-AC
configfile: pyproject.toml
plugins: golden-0.2.2
collected 4 items                                                                                                                                                                  

golden_test.py::test_translator_and_machine[golden/cat.yml] PASSED                                                                                                           [ 25%]
golden_test.py::test_translator_and_machine[golden/hello.yml] PASSED                                                                                                         [ 50%]
golden_test.py::test_translator_and_machine[golden/hello_user_name.yml] PASSED                                                                                               [ 75%]
golden_test.py::test_translator_and_machine[golden/prob1.yml] PASSED                                                                                                         [100%]

================================================================================ 4 passed in 1.73s ================================================================================
```

```text
| ФИО                             | алг             | LoC | code инстр. | инстр. | такт. |
| Валиев Ришат Ильшатович         | cat             | 24  | 23          | 191    | 907   |
| Валиев Ришат Ильшатович         | hello           | 40  | 51          | 268    | 1348  |
| Валиев Ришат Ильшатович         | hello_user_name | 110 | 139         | 820    | 4102  |
| Валиев Ришат Ильшатович         | prob1           | 60  | 56          | 1937   | 8992  |
```
