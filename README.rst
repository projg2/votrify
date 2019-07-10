=========================================================
Votrify -- Community validator of Gentoo election results
=========================================================

*Why trust when you can votrify?*


How can Gentoo elections be verified?
=====================================
Along with Gentoo Council and Trustee election results, the master
ballot containing all (pseudonymized) votes is published.  This makes it
possible to inspect the election results in three aspects:

1. Everyone can verify that the eligible voter list is correct and that
   the number of votes collected matches the number of eligible voters
   (i.e. that there are no extraneous votes included).

2. Everyone can count the votes and verify the correctness of published
   results.

3. Voters can verify that their own vote has been recorded correctly.

However, this does not confirm that other votes in the master ballot
are legitimate.  In order to verify this, all voters would have to
verify their own votes and provide a cryptographically verifiable
confirmation of that.  This is where Votrify comes.


What does Votrify do?
=====================
Votrify is a suite of tools to communally verify election results.
Currently, it consists of two scripts:

- ``make-confirmation.py`` that produces a signed confirmation that
  your vote was included in master ballot along with your election
  results,

- ``verify-confirmations.py`` that verifies signed confirmations
  from multiple voters in order to determine how many votes were
  verified.

By combining those tools, you can establish how many votes in the master
ballot were verified, and therefore how reliable the election results
are.


How to use it?
==============
Firstly, you need to obtain election files.  Those are both attached
to election result mails, and are found in elections repository
[#ELECTIONS]_.  You specifically need at least the ballot
(``ballot-*``), master ballot (``master-*``) and the voters list
(``voters-*``).

Secondly, if you voted, then you need your vote file and confirmation
id.  The former is found on dev.gentoo.org as ``.ballot-*-submitted``,
the latter you should have gotten by mail.

Thirdly, you need to have OpenPGP keys of all voters, fetched
and verified.  Using Gentoo Authority Key is recommended for that
purpose  [#AUTHKEY]_.

Fourthly, you need ``countify`` script and ``Votify.pm`` from elections
repository.  If you checked out Votrify repository with submodules,
the script will find them itself.  Otherwise, you should specify
a path to them via ``-s``.

When you have all the files needed, use ``make-confirmation.py`` to
verify your vote and produce OpenPGP-signed confirmation.  You need
to pass the ballot file as ``-b``, master ballot as ``-m``, your
confirmation id as ``-c`` and your vote as ``-v``.  By default,
the confirmation is output to stdout::

    $ ./make-confirmation.py -b ballot-council-201806 \
      -m master-council-201806 -c 1234 \
      -v .ballot-council-201806-submitted  
    -----BEGIN PGP SIGNED MESSAGE-----
    Hash: SHA512

    {"master_hash": "z4PhNX7vuL3xVChQ1m2AB9Yg5AULVxXcg/SpIdNs6c5H0NE8XYXysP+DGNKHfuwvY7kxvUdBeoGlODJ6+SfaPg==", "results": [["dilfridge"], ["ulm"], ["k_f"], ["williamh"], ["slyfox"], ["leio", "whissi"], ["amynka"], ["tamiko"], ["rich0"], ["soap"], ["bman"], ["_reopen_nominations"]]}
    -----BEGIN PGP SIGNATURE-----
    Comment: This is a Votrify election vote confirmation

    iQGTBAEBCgB9FiEEx2qEUJQJjSjMiybFY5ra4jKeJA4FAl0EpYFfFIAAAAAALgAo
    aXNzdWVyLWZwckBub3RhdGlvbnMub3BlbnBncC5maWZ0aGhvcnNlbWFuLm5ldEM3
    NkE4NDUwOTQwOThEMjhDQzhCMjZDNTYzOUFEQUUyMzI5RTI0MEUACgkQY5ra4jKe
    JA5VqQf+JmJQxUlszsIqCvbfDIS+gWKtwKfXneIZpz+Otoin3J0ylSN5XC0MVgV/
    WAz3qIuTenzwUHvaIPnpZwCa8HU+KccEoptXC9wjmRLVfblQZxB77W4wzCaMs/hc
    dewhpiZS2COp2yppKR1lv/ae1FX7d8nTVkANucCfywjHTLgLb1zAm/5fZyOFzBiV
    Z3H5M2d6iypK8XwxSU2uBDCw2qxvr9L0hj4x+NOPPPilYpzG4hpJgcoOP9u+0Li2
    6m0PwTwkY5I9zyzpnqN33aG8Hv0hLCsk5o32DF5mK40timdJWLHVLXqpsHxxYrwb
    dE+9WLQkg4wMj+4sV7ehWeG53cifaA==
    =XThI
    -----END PGP SIGNATURE-----

If you haven't voted, you should pass ``-n`` instead of ``-v``
and ``-c``.

If the verification fails, a short error is output instead::

    $ ./make-confirmation.py -m master-council-201806 -c 1234 \
      -v .ballot-council-201806-submitted  
    Vote mismatch found (old = your vote, new = vote recorded):
    <here goes the diff>

Note that you need to use OpenPGP key that has your ``@gentoo.org``
e-mail address in one of the UIDs.

Save your confirmation into a file and upload it to some common storage.
Others should upload their confirmations there as well.  Afterwards,
fetch all confirmations found and verify them using
``verify-confirmations.py``.  This script takes a list of files
as positional arguments and a voters list as ``-v``::

    $ ./verify-confirmations.py -v voters-council-201806 out/*
    Verified 1 out of 183 known voters (election is 0.55% verified)

The script will verify that each confirmation is signed by a key that
has a respective voter address in one of the UIDs, that is fully trusted
by you and that no voter submitted more than one confirmation.  It will
also make sure that all voters received the same master ballot, and that
their election results match.


References
==========

.. [#ELECTIONS] Gentoo Elections control data
   (https://gitweb.gentoo.org/proj/elections.git/)

.. [#AUTHKEY] Project:Infrastructure/Authority Keys
   (https://wiki.gentoo.org/wiki/Project:Infrastructure/Authority_Keys)
