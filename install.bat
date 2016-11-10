WHERE /q pip3
IF %ERRORLEVEL% EQU 0 (
    pip3 install -e .
) ELSE (
    WHERE /q pip
    IF %ERRORLEVEL% EQU 0 (
        pip install -e .
    ) ELSE (
        echo "Could not find a copy of python pip on this system. Aborting"
    )
)
