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
  your vote was included in master ballot,

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
[#ELECTIONS]_.  You specifically need at least the master ballot
(``master-*``) and the voters list (``voters-*``).

Secondly, you need your vote file and confirmation id.  The former
is found on dev.gentoo.org as ``.ballot-*-submitted``, the latter you
should have gotten by mail.

Thirdly, you need to have OpenPGP keys of all voters, fetched
and verified.  Using Gentoo Authority Key is recommended for that
purpose  [#AUTHKEY]_.

When you have all the files needed, use ``make-confirmation.py`` to
verify your vote and produce OpenPGP-signed confirmation.  You need
to pass the master ballot as ``-m``, your confirmation id as ``-c``
and your vote as ``-v``.  By default, the confirmation is output
to stdout::

    $ ./make-confirmation.py -m master-council-201806 -c 1234 \
      -v .ballot-council-201806-submitted  
    -----BEGIN PGP SIGNED MESSAGE-----
    Hash: SHA512

    {"master_hash": "czhkJ3oblwxWxKfDZ2k5E6hY+dXps2Qe2zto79CDQC5fPetAGKnA/xecnblPfRmX/Cf4jXJQqHYYv760yB/r/Q=="}
    -----BEGIN PGP SIGNATURE-----
    Comment: This is a Votrify election vote confirmation

    iQGTBAEBCgB9FiEEx2qEUJQJjSjMiybFY5ra4jKeJA4FAl0Ej+NfFIAAAAAALgAo
    aXNzdWVyLWZwckBub3RhdGlvbnMub3BlbnBncC5maWZ0aGhvcnNlbWFuLm5ldEM3
    NkE4NDUwOTQwOThEMjhDQzhCMjZDNTYzOUFEQUUyMzI5RTI0MEUACgkQY5ra4jKe
    JA4QoQf9H5vFE/ABRwdtNafST4cuqq/gVr+KX+AkgreF1lapvDBxlp6yzW0V1lMw
    DJw6YWatnE7SwPO+Zc1gPaG0Kk2QT/UC7BaM/X0CEItVsK3CcuV5L+rxDMq6bZ8j
    RcKhSEbgQsqUhZ/uEDezPP48cSao+ycK4cU8FLONRH5lp/HlilDO9f7Nb33RNKD3
    cbT8BGQvR4+2WLu4/N5qg2WWlH0oQJ0yesQpb2U0c5bSBxCIPh+mb0eUZFKrr4Qx
    1hnw3svOk5NJ6Tzi9JETPAzox3U/QTgYWxl1CfSQ1Gf5XCitUZHUTvN020QyHB3e
    PfbG8HAPU5z4eejB53W8UQ3z7xCn7Q==
    =rwjg
    -----END PGP SIGNATURE-----

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
by you and that no voter submitted more than one confirmation.


TODO
====
- Verify election results as well.


References
==========

.. [#ELECTIONS] Gentoo Elections control data
   (https://gitweb.gentoo.org/proj/elections.git/)

.. [#AUTHKEY] Project:Infrastructure/Authority Keys
   (https://wiki.gentoo.org/wiki/Project:Infrastructure/Authority_Keys)
