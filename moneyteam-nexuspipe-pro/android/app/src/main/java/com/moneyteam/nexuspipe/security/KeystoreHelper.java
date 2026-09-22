package com.moneyteam.nexuspipe.security;

import java.security.KeyStore;
import java.security.PublicKey;
import java.security.cert.Certificate;

/**
 * AndroidKeyStore helper for the MONEYTEAM / NexusPipe Android client.
 *
 * Hardware-backed keys live inside AndroidKeyStore and never leave secure
 * hardware. This helper loads the store and exposes the public key of a
 * certificate stored under a given alias.
 */
public final class KeystoreHelper {

    private static final String ANDROID_KEYSTORE = "AndroidKeyStore";

    private KeystoreHelper() {
        // utility class
    }

    /**
     * Loads AndroidKeyStore and returns the public key of the certificate
     * stored under {@code alias}.
     *
     * @param alias the keystore alias (e.g. "nexuspipe-release")
     * @return the certificate's public key
     * @throws IllegalStateException if no certificate exists for the alias
     * @throws Exception if the keystore cannot be loaded
     */
    public static PublicKey getPublicKey(String alias) throws Exception {
        KeyStore keyStore = KeyStore.getInstance(ANDROID_KEYSTORE);
        keyStore.load(null);
        Certificate cert = keyStore.getCertificate(alias);
        if (cert == null) {
            throw new IllegalStateException("No certificate in AndroidKeyStore for alias: " + alias);
        }
        return cert.getPublicKey();
    }
}
