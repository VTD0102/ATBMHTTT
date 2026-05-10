rule RansomwareSimulator_Demo {
    meta:
        description = "Detect ransomware simulator used for academic demo"
        author = "ATBMHTTT Demo Project"
        severity = "CRITICAL"
        type = "simulator"

    strings:
        $sig1 = "RANSOMWARE_SIMULATOR_DEMO_SAFE" ascii
        $sig2 = "RansomwareSimulator" ascii
        $sig3 = "ENCRYPTED_EXT = \".encrypted\"" ascii

    condition:
        any of them
}

rule EncryptedFilePattern {
    meta:
        description = "File with Fernet encryption token header"
        severity = "HIGH"
        type = "encrypted_data"

    strings:
        $fernet_header = { 67 41 41 41 41 }

    condition:
        $fernet_header at 0
}

rule WindowsSafeDemoTransform {
    meta:
        description = "Detect Windows-safe file transform used for academic demo"
        severity = "CRITICAL"
        type = "simulator"

    strings:
        $header = "ATBMHTTT_DEMO_ENCRYPTED_V1" ascii
        $marker = "DEMO_ENCRYPTED_EXT" ascii
        $backup = ".demo_original" ascii

    condition:
        any of them
}
rule RansomNoteHTML {
    meta:
        description = "Detect ransom note HTML page"
        severity = "HIGH"
        type = "ransom_note"

    strings:
        $note1 = "YOUR FILES HAVE BEEN ENCRYPTED" ascii wide
        $note2 = "Bitcoin" nocase ascii
        $note3 = "decrypt" nocase ascii

    condition:
        ($note1 or $note2) and $note3
}
