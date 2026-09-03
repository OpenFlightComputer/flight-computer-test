# microSD component

The automatic test requires an initially empty socket, debounces insertion,
initializes the card in SPI mode, writes eight deterministic raw sectors near
the end of the medium, reads them back, checks bytes and CRC-32, and zero-fills
the test area. It does not use or preserve a filesystem.

Failures are emitted before terminal completion with the exact command or media
stage, a machine-readable reason, and a numeric detail. During initialization
this distinguishes SPI setup and clocks, CMD0, CMD8/R7, CMD55/ACMD41, CMD58/OCR,
CMD16, CMD9/CSD, and the high-speed transition. Later stages distinguish CMD24
write/data acceptance, CMD17 read/token handling, content/checksum mismatch,
card removal, and cleanup.
