# Extra

## Compiling nand2tetris_simulator

```bash
git clone https://github.com/nand2tetris/nand2tetris_simulator.git
cp build-simulator.py nand2tetris_simulator
cd nand2tetris_simulator
python build-simulator.py
```

## Force simulator to start with English language

```bash
# Download the Nand2tetris Software Suite on https://drive.google.com/file/d/1xZzcMIUETv3u3sdpM_oTJSTetpVee3KZ/view
cp patch-java-lang.py ../toolkit/tools
cd ../toolkit/tools
python patch-java-lang.py
```
