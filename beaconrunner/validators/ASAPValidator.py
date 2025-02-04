from typing import Optional, Sequence

from ..specs import (
    Attestation, SignedBeaconBlock, config,
    SLOTS_PER_EPOCH,
)
SECONDS_PER_SLOT = config.SECONDS_PER_SLOT

from ..validatorlib import (
    BRValidator, SyncCommitteeBundle,
    honest_attest, honest_sync_committee, honest_propose
)

class ASAPValidator(BRValidator):
    """
    Validator behaviour attesting and proposing honestly, following the honest validator
    specs.
    """
    # Always $lash and prosper!

    validator_behaviour = "asap"

    def attest(self, known_items) -> Optional[Attestation]:
        """
        Returns an honest `Attestation` as soon as at least four seconds (`SECONDS_PER_SLOT / 3`)
        have elapsed into the slot where the validator is supposed to attest or the validator
        has received a valid block for the attesting slot.
        Checks whether an attestation was produced for the same slot to avoid slashing.

        Args:
            self (ASAPValidator): Validator
            known_items (Dict): Known blocks and attestations received over-the-wire (but perhaps not included yet in `validator.store`)

        Returns:
            Optional[Attestation]: Either `None` if the validator decides not to attest,
            otherwise an honest `Attestation`
        """

        # Not the moment to attest
        if self.data.current_attest_slot != self.data.slot:
            return None

        time_in_slot = (self.store.time - self.store.genesis_time) % SECONDS_PER_SLOT

        # Too early in the slot / didn't receive block
        if not self.data.received_block and time_in_slot < 4:
            return None

        # Already attested for this slot
        if self.data.last_slot_attested == self.data.slot:
            return None

        # honest attest
        return honest_attest(self, known_items)

    def sync_committees(self, known_items) -> Optional[Sequence[SyncCommitteeBundle]]:
        """
        Returns an honest list of `(sync_committee_index, sync_subcommittee_index, SyncCommitteeSignature)` as soon as
        at least four seconds (`SECONDS_PER_SLOT / 3`)
        have elapsed into the slot where the validator is supposed to attest or the validator
        has received a valid block for the attesting slot.
        Checks whether an attestation was produced for the same slot to avoid slashing.

        Args:
            self (ASAPValidator): Validator
            known_items (Dict): Known blocks and attestations received over-the-wire (but perhaps not included yet in `validator.store`)

        Returns:
            Optional[Sequence[SyncCommitteeBundle]]: Either `None` if the validator decides not to produce sync committee signatures,
            otherwise an honest list of sync committee bundles
        """

        # Not the moment to attest
        if len(self.data.current_sync_committee) == 0:
            return None

        time_in_slot = (self.store.time - self.store.genesis_time) % SECONDS_PER_SLOT

        # Too early in the slot / didn't receive block
        if not self.data.received_block and time_in_slot < 4:
            return None

        # Already attested for this slot
        if self.data.last_slot_sync_committee == self.data.slot:
            return None

        # honest sync committee
        return honest_sync_committee(self, known_items)

    def propose(self, known_items) -> Optional[SignedBeaconBlock]:
        """
        Returns an honest `SignedBeaconBlock` as soon as the slot where
        the validator is supposed to propose starts.
        Checks whether a block was proposed for the same slot to avoid slashing.

        Args:
            self (ASAPValidator): Validator
            known_items (Dict): Known blocks and attestations received over-the-wire (but perhaps not included yet in `validator.store`)

        Returns:
            Optional[SignedBeaconBlock]: Either `None` if the validator decides not to propose,
            otherwise a `SignedBeaconBlock` containing attestations
        """

        # Not supposed to propose for current slot
        if not self.data.current_proposer_duties[self.data.slot % SLOTS_PER_EPOCH]:
            return None

        # Already proposed for this slot
        if self.data.last_slot_proposed == self.data.slot:
            return None

        # honest propose
        return honest_propose(self, known_items)
