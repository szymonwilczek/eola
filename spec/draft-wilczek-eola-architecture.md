---
# SPDX-License-Identifier: CC-BY-4.0
# Copyright (C) 2026 Szymon Wilczek
title: End-Of-Life Attestation (EOLA) Architecture
abbrev: EOLA Architecture
docname: draft-wilczek-eola-architecture-00
category: info
ipr: none
submissiontype: independent
stand_alone: yes
keyword:
  - game preservation
  - remote attestation
  - key escrow
author:
  -
    fullname: Szymon Wilczek
    email: swilczek.lx@gmail.com

normative:
  RFC8032:

informative:
  RFC5869:
  RFC9334:
  TPM2:
    title: Trusted Platform Module 2.0 Library
    target: https://trustedcomputinggroup.org/resource/tpm-library-specification/
    author:
      - org: Trusted Computing Group
  SHAMIR:
    title: How to Share a Secret
    author:
      - ins: A. Shamir
        name: Adi Shamir
    date: 1979-11
    seriesinfo:
      "Communications of the ACM": "vol. 22, no. 11, pp. 612-613"
      DOI: 10.1145/359168.359176
  FELDMAN:
    title: A Practical Scheme for Non-interactive Verifiable Secret Sharing
    author:
      - ins: P. Feldman
        name: Paul Feldman
    date: 1987-10
    seriesinfo:
      "28th Annual Symposium on Foundations of Computer Science": "pp. 427-438"
      DOI: 10.1109/SFCS.1987.4

--- abstract

End-Of-Life Attestation (EOLA) lets a game remain playable after its
publisher stops operating it. While the game is operated, the publisher
signs the material that players and community servers need to continue
without it: a periodic heartbeat, licenses, player progress records, the
list of official server builds, and an escrowed copy of the server
program whose key is held by independent trustees. This document
describes the roles, documents, keys, and life cycle that the EOLA
protocol documents build on. It defines no wire format.

--- middle

# Introduction

A game with online components depends on services its publisher runs:
servers that host play, accounts that hold progress, and store or license
checks. When the publisher stops running them, the game stops working,
including copies that players have already bought.

EOLA prepares a game for that event from its first release. The
publisher signs, while it still operates the game, everything a player
and a community server need afterwards, and ships it with the game or
publishes it where anyone can copy it. When the publisher stops, either
by announcing the end of life or by falling silent, every client reaches
the same conclusion from signed data alone and switches to community
operation.

This document gives the architecture: the roles ({{roles}}), the keys
and identity of a game ({{keys}}), the signed documents ({{documents}}),
the life cycle of a game as a client sees it ({{life-cycle}}), and the
four layers that carry a game past its publisher ({{layers}}). Each layer
is specified in its own document, which defines its formats, processing
rules, and error codes.

## Design Principles

Three properties hold across all layers:

Signed documents, untrusted carriers:
: Everything a client acts on is a document signed by a key of the
  publisher, or by a key that a document signed by the publisher names.
  Any party can carry a document: an official server, a community
  server, a directory, a mirror, an archive, or removable media. No
  carrier has to outlive the publisher.

Prepared at release:
: A game contains, from its first release, every key, rule, and code path
  it needs after the publisher stops. What cannot ship with the game, the
  server program, is held in escrow ({{escrow}}).

Nothing reported:
: EOLA has no telemetry, no accounts of its own, and no service whose
  absence stops the protocol from working.

# Conventions and Terminology

{::boilerplate bcp14-tagged}

The following terms are used in all EOLA documents with the meanings
given here.

Game:
: A program distributed to players, together with the server program it
  connects to, identified by its game identifier.

Publisher:
: The party that releases and operates a game and holds its root key.

Root key:
: The Ed25519 {{RFC8032}} key pair of a game whose public half ships with
  the game. It is kept offline and signs only operational key
  certificates, revocations, the game policy, server manifests, the
  escrow manifest, and the end-of-life notice.

Game identifier:
: The SHA-256 digest of the public root key. It is the only name of a
  game in EOLA; no registry of names exists.

Operational key:
: An Ed25519 key pair certified by the root key for a limited validity
  period. It signs heartbeats, licenses, passports, and official server
  registrations.

Revocation:
: A statement signed by the root key that withdraws the certificate of
  an operational key, including for documents that key signed earlier.

Heartbeat:
: A document signed by an operational key that states the official
  service is alive until a stated time.

Grace period:
: The number of days, fixed by the publisher in the game policy, that a
  client waits after the last heartbeat expires before it enters
  community operation.

Game policy:
: The parameters of a game chosen by the publisher at release and signed
  by the root key, including the grace period.

End-of-life notice:
: A document signed by the root key that announces when official
  operation ends.

Player key:
: An Ed25519 key pair generated by the client and kept with the player's
  saved data.

License:
: A document signed by an operational key that binds a player key to a
  game.

Passport:
: A document signed by an operational key that records a player's
  progress in a game, bound to a player key.

Directory:
: A service that accepts registrations of game servers and returns the
  list of servers registered for a game identifier.

Official server:
: A game server whose registration is signed by an operational key.

Community server:
: A game server run by a party other than the publisher.

Operator:
: The party that runs a community server.

Appliance:
: A read-only operating system image that runs a server program on a
  machine with a TPM {{TPM2}} and gives its operator no means to log in
  or change the running software.

Trusted base:
: An appliance base image, without a server program, whose measurements
  are listed as trusted.

Server manifest:
: A document signed by the root key that lists the measurements of every
  official build of the server program.

Verified server:
: A server whose attestation evidence a client has appraised as an
  appliance running a trusted base and a build listed in the server
  manifest.

Unverified server:
: A server for which a client has no such appraisal. The term makes no
  claim that the server software is modified.

Escrow:
: The encrypted server program, published from release, and the secret
  sharing of its key among trustees.

Trustee:
: A party that holds one share of the escrow key and publishes it when
  the conditions in {{escrow}} are met.

Client:
: The part of a game that runs on a player's device and implements EOLA.

# Roles {#roles}

The publisher generates the root key, releases the game, signs all
documents of the official service, and builds the server manifest and
the escrow. After the end of life, the publisher takes no further part.

The client keeps the player key, the license, the latest passport, and
the latest heartbeat. It decides the state of the game ({{life-cycle}}),
retrieves server lists from directories, and appraises the evidence of
servers it connects to.

An official server hosts play while the publisher operates the game. It
registers with directories and passes the current heartbeat to every
client that connects to it.

A community server hosts play after the end of life, or earlier when the
game policy permits community servers from release. Its operator either
runs the appliance on a machine with a TPM, which makes it eligible to be
a verified server, or runs the server program on any machine, which makes
it an unverified server.

A directory keeps server registrations for any number of games, keyed by
game identifier. Any party can run one. A game ships with the addresses
of several directories, and heartbeats and end-of-life notices can name
more.

A trustee holds a share of the escrow key, watches the heartbeat of the
game, and publishes its share when official operation has ended.

# Keys and Game Identity {#keys}

A game has one root key for its whole life. The client trusts exactly
the public root key it ships with, and every chain of trust a client
evaluates ends at that key.

The root key certifies operational keys. A client accepts a document
signed by an operational key only together with a certificate of that key
signed by the root key and valid at the time of the document.

A revocation is signed by the root key and is valid on its own, so it
can reach a client inside a heartbeat, a server greeting, or a game
update. A client MUST keep every revocation it has accepted for the life
of the installation, and MUST reject every document signed by a revoked
operational key, including documents it accepted before the revocation.
Because a revocation needs the root key, a stolen operational key cannot
revoke the other operational keys of the game.

Loss of the root key ends the ability of the publisher to sign a server
manifest or an end-of-life notice. It does not stop the life cycle: the
last heartbeat expires and clients enter community operation after the
grace period.

# Documents {#documents}

{{doc-table}} lists the documents of EOLA, the key that signs each, and
where a client obtains it. Every document names the game identifier it
belongs to, and a client rejects a document that names another game.

| Document            | Signed by       | Obtained from                          |
|---------------------|-----------------|----------------------------------------|
| Game policy         | root key        | the game files                         |
| Server manifest     | root key        | heartbeat reference, any carrier       |
| End-of-life notice  | root key        | heartbeat, servers, any carrier        |
| Revocation          | root key        | heartbeat, servers, game updates       |
| Heartbeat           | operational key | official servers, directories, mirrors |
| License             | operational key | publisher service, once per player     |
| Passport            | operational key | publisher service, periodically        |
| Server registration | operational key | directories                            |
| Escrow manifest     | root key        | the game files, any carrier            |
{: #doc-table title="EOLA Documents"}

A heartbeat carries a sequence number that increases with every
heartbeat of a game. A client keeps the heartbeat with the highest
sequence number it has verified and ignores any heartbeat with a lower
one, so a carrier cannot move a client back to an older state by
replaying an old heartbeat.

# Life Cycle {#life-cycle}

A client keeps the game in one of three states:

OFFICIAL:
: The client holds a heartbeat that is valid at the current time. The
  game behaves as the publisher operates it.

GRACE:
: The last verified heartbeat has expired, and the grace period has not
  passed. Official servers remain usable if they still answer, and the
  client tells the player how long the publisher has been silent.

COMMUNITY:
: The grace period has passed since the last verified heartbeat
  expired, or a verified end-of-life notice has reached its shutdown
  time. The client lists community servers, accepts them for play with
  the player's passport, and applies the end-of-life provisions of the
  game policy.

A client moves from GRACE back to OFFICIAL when it verifies a heartbeat
with a higher sequence number that is valid at the current time. A client
MUST NOT leave COMMUNITY. Once the escrow can be opened, a return of the
publisher cannot close it again; servers of a returning publisher appear
again as official servers next to the community servers.

The transition depends on the clock of the player's device. A player who
sets the clock forward reaches COMMUNITY early on that device. This gains
nothing a player cannot already do with a private server: before the end
of life, the escrow is closed and no community server can run a build
from the server manifest.

## Announced End of Life

The publisher signs an end-of-life notice that gives the shutdown time,
the time until which final passports are issued, the directories that
continue after the shutdown, and the license under which the server
program may be run and distributed after the shutdown. A client that
verifies the notice informs the player before the shutdown and enters
COMMUNITY at the shutdown time without waiting for the grace period.

## Unannounced End of Life

When heartbeats stop, the last one expires, clients enter GRACE, and
after the grace period they enter COMMUNITY. Every client reaches the
same state from the same signed heartbeat and the same game policy,
with no message from the publisher.

# Layers {#layers}

## Heartbeat and Directories

The heartbeat tells clients and trustees that official operation
continues. Official servers attach the current heartbeat to their
greeting, so a client that plays on an official server receives it even
when every web address of the publisher is unreachable. A client that
retrieves a heartbeat over the network sends a request that carries no
identifier of the player.

A game locates servers through directories and has no fixed server
address. A server proves to a directory that it receives traffic at the
address it registers, and a directory returns the list of registrations
for a game identifier. A directory list is untrusted: a client checks
the signature of an official server registration and the attestation
evidence of a server before it shows either property to the player.

## License and Passport

A license binds a player key to a game, so a client can check the right
to play without contacting the publisher. A store or platform check can
coexist with it while the publisher operates the game; the game policy
states whether the client stops requiring that check in COMMUNITY.

A passport records the progress of a player in a schema chosen by the
publisher. The client keeps the latest passport it has received. A
community server accepts a passport when the publisher's signature on it
verifies and the player proves possession of the player key named in
it. A community server that has accepted a passport for a player key
rejects later passports for the same player key, so a player cannot
restore an older state of the same character on that server.

## Trust Without the Publisher {#trust}

A player on a community server needs to know whether the server runs an
official build of the server program and whether its operator can alter
it. The operator of a community server has full control of its machine,
so a report produced by software on that machine is not evidence against
the operator. EOLA uses only evidence the operator cannot forge without
attacking the hardware: measurements of the boot chain and of the server
program, recorded by the TPM before the system runs and signed by the
TPM in a quote. This follows the remote attestation architecture of
{{RFC9334}}, with the appliance as attester and the client as verifier
and relying party.

The appliance is built in two layers. The trusted base is built
reproducibly, and its measurements are published as a signed list. The
server program is a separate read-only partition whose measurement must
appear in the server manifest of the game. The operator configures the
server only through a fixed set of settings that are measured as well,
and has no login, shell, or means to add a process or read the memory
of the server.

When a client joins a server, it appraises a quote over a fresh nonce
from the client and the public key of the session channel. The client
establishes that the quoting key resides in a TPM whose endorsement
certificate chains to a TPM manufacturer root shipped with the game, and
it does so without any certificate authority run by the publisher. It
then replays the measurement log against the quoted values and checks
them against the trusted base list and the server manifest. The whole
session runs over the channel whose key the quote covers.

A client that cannot complete this appraisal treats the server as an
unverified server. Unverified servers remain playable; the client shows
the player which servers are verified.

## Escrow {#escrow}

The server program is the one part of a game that cannot ship to
players in usable form before the end of life. At release, the
publisher generates an escrow key and divides it among trustees with a
threshold secret sharing scheme {{SHAMIR}}, publishing commitments that
let anyone check a share {{FELDMAN}}. Each build of the server program is
encrypted under a key derived from the escrow key and the build version
{{RFC5869}}, so trustees receive their shares once for the life of the
game. The ciphertexts are public from release, and the escrow manifest,
signed by the root key, lists their digests and the trustees.

A trustee publishes its share when it verifies an end-of-life notice
whose shutdown time has passed, or when the grace period has passed
since the last heartbeat it verified expired. Any party that collects
the threshold number of shares reconstructs the escrow key, decrypts a
build, checks it against the escrow manifest, and runs it, in the
appliance or as an unverified server. The escrow also carries the
license under which the server program may be run and distributed after
the end of life.

# Privacy Considerations

EOLA collects no data about players. A directory sees the network
address of a client that requests a server list. An official server sees
what the game sends it during operation. A community server sees the
public player key and the passport a player presents to it. The
endorsement certificate of a server TPM is visible to every client that
appraises the server; a server is public by its nature, so this links
only the server to its own hardware.

# Security Considerations

This section states what the architecture guarantees and what it does
not. Each layer document states the threats to that layer.

A party without an operational key cannot extend the life of the
official service, and a party without the root key cannot announce the
end of life early. A party without these keys can affect the state of a
client only by withholding heartbeats from it, which moves that client
toward COMMUNITY, never away from it.

A stolen operational key lets the thief sign heartbeats, licenses, and
passports until the publisher revokes it. Revocation needs the root key,
so the security of the root key bounds the damage. Passports signed by a
revoked key become invalid and have to be issued again, which is
possible only while the publisher operates the game.

Trustees that reach the threshold together can open the escrow before
the end of life. The publisher limits this risk by the choice of the
threshold and of trustees that are independent of each other and of the
publisher.

The binding of the quote to the session channel key prevents a server
from relaying the evidence of a genuine appliance while serving players
from a different machine. A verified server does not protect against an
attacker with physical access to the TPM bus, firmware that records
false measurements, remote exploitation of the kernel or the server
program, or cheating on the client side. A verified server means that
the server started an official build in an appliance its operator cannot
log in to.

# IANA Considerations

This document has no IANA actions.

--- back

# Change Log
{:numbered="false"}

draft-wilczek-eola-architecture-00:
: Initial version.
