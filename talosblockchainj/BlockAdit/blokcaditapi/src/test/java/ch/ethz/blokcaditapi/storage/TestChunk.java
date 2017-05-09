package ch.ethz.blokcaditapi.storage;

import org.junit.Test;

import java.security.KeyPair;
import java.util.Random;

import ch.ethz.blokcaditapi.storage.chunkentries.DoubleEntry;

import static ch.ethz.blokcaditapi.storage.Util.bytesToHexString;
import static ch.ethz.blokcaditapi.storage.Util.hexStringToByteArray;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * Created by lukas on 08.05.17.
 */

public class TestChunk {

    // nice xD
    private static String pyEncoded = "4a7abfdd6932f5de3e41abe953c042e14ad08338f72ced8afe43fa27878d50430100000059f7a5a9de7a44ad0f8b0cb95faee0a2a43af1f99ec7cab0" +
            "36b737a4c0f911bb3d070000b5233948aaa8c895325610f449b4b5627e6a001f40539daa6e5c110a0a6f2f216a579b9ee104be6aa85a45818fcb75d91f8a3dbb04e17bfa2ca96e0a174ea4b" +
            "66f560020a5d98cd9034753dce6335100ae14f794f46e064254b0c463f7618e1feaf9c95cc9f53447618bdd82d4002dde8c53fdabfa67621269b86fd16799c94712121929879fe59db50d0cd" +
            "2ec55c6ec850eb44981caa9ec2d340958b3d73332f6185b72fae6488620700411d7296c698458eceabf7dbf1819deb68091a30c8f4d2b987603862e39c893ad4636db51d6275087572b64fc0980172" +
            "21278e669188321b2bafe460e67be97e710393ab8f5cc6f2ef34ea5e1ce3c5754e282b890f3bf51e138288ad33ed88d727aa8013d7c6f5043f0de625f1c7a001deccfa1302254f0708054ed4ee1d160deaaf" +
            "29c01ae7878fff698763af219e390ea31c835e40b591dbf20f8072cdc8a7986336c4e283993e4c907b5af45788a13f5af34bfa53d416424d027867c2888216ae7056d3c4a6c5167c14c04bc60ba354667130" +
            "bbb00cc194724c453266b4f15da2025a0c51ce800576ca7261138e17a66459c88720c1b0f0589eb6a50caccbdc00e7fd555c4b42cbd8cd8c355feeb0a927db4e7f38e6078640f58a4674fbec7fd56bfbe" +
            "52035e63fdb70c9dd30ec67b55548775e7ed5caa2acb5ee6aca236e2b1f2c9d1482d176cdd5696ed047fd23838822691f648bd2cab6a902a36d795c759cf4a96ca747250903b1ab47780928973c1f298" +
            "afb577e806b0937dab993fd4dfff742106823f581d4150481d60226fdf7b97e4aa58fe6981f3d8b148af722bf6141b704281c43dd05ac8bd1d0d8fe138d4811b9ab317c12f94cd1a5d67a7d4c5c69002c" +
            "553a636596f1bd1201794010b135074ef8227518bf93a968b182dc41dcb70251daa7560f055030dec46e12fc644dc0cd43842c332e13a3752edc3b4bff0d66d8b07c9018c51eab113fa5bdf81cea874b0b" +
            "8f5364ff5e7e50caeb23426e4ce8cadff523d5044202d7a75a1162c082495fb2acc53b494a83afea34ebb402f296d94f2a9ea36f4c4803bd8f1b04cb122f0d150e3db96310a5bbc4f004f8351fb174fea80" +
            "686e6af233049c7dca8d42c61213cdea2a8c8dd17f624f4799a315979c6672c5d544f138f4593e928894f42a0abbcae2262798e92cdec04db8b229b9cf34813ea5782948bb6cc6ee3343211ec2813afce05d" +
            "0a67ba093fe88c6e02b5263aa9fc2dd867e25e5f22a5e2e528153ad96f7a4eeaee9fc06f35a18edc49026168ba14c6ba058c738c6bb0fbc3330b74e69f616ca7754a11b983e68e970a50d7a4338539cb60248" +
            "2d847598ea2b23ad9b0c6d74cbb4c64fe120478e132b48dc6b88f36449e2732839ea90ff2037db7f3ecaa9fdd25956266031debb8cd0f104eda4e84b47e011892c1434a141fb61f0fba6ccec3c32ffd2e94b6a" +
            "b3f2ed0c46ef964c6272faf9d2e5dbf200ff01846f1dc03b8ca80b82f5c145579f1b3c8f2f792e2e767d9f2b1633fbc8a4bd594d8a7d219f4d4cd8dfadeb7fc3fc3d4f2e562007b894ad6252ed4bb6442619e17" +
            "794ef002bf9f01296397d0543681c98cc6092bbb5b6c55c5188c9ea784a445f36f87c54f83e9b3c402c89ffc3d3090ba99e8d55b62b329dc2d100d4c64ac9726586160af3a46393aa80f17b0781a441610691b88235" +
            "842e71e000e6edbca4a2973bf87ba27dc8fedd3914a6ab15e7145370729a6266b7a2eb9efae5abe9e196c18fb4ef744dd5039d0a2e53954bf9991c0c7557ce9354e53c846a2ec45ea9a2aa2789f5cbc1bcce6e500" +
            "de40f38b12fe5a5062bb1eb61453d26b6637957179f082857153e70e36e35b0d614dd551cdc4c35e89925a7654ebbb19706bfc2395baa6ea7968608e703f8a94c1b049c7041e9d9dab3c697eb667c682f9559e2d" +
            "7adabca2f93ba4ae3b3751193ab163db4d33dd9eec1d4d5224390d692ce24266c977d3144c5d6dd128e85d35f406ee28c09c50e79869a0f0eea91fdc9a4b8a8039732e3a6fe95dab6a9d42f5e5839bbec730149" +
            "52dcf9a3572a2a0ce5a5dbddfb244afdc688fe1e7e6424ea4f536dd51d4a8c0167acb2b073e70813a67c61a685a47322123515b742d2b20459fcdee02b48afe6953df692e1dfe4fb99acb246e34c03854374e3" +
            "74aebe3b1702f16cad84b92a5e31a870154b66f6aac88969549453a39f67e8bf07aed0d43e71267b0ad53adca42adaa4200f96209e4aa24ab3bf0aebe1f8bf221e1cdac94aa6bcb9f50114e212df30d84f26ed" +
            "2ea6de412155d86740d6cf5698e9c544b01d37535c777dd03908d65bae7676ef05c0dd0ce073350fe029fae2ebfcbc7002b0a7a9b474d0ea00225ad7c342018c23d4a8ad636d5bb7ae15550345d1c2c9c7b" +
            "55d4e16c43c55e1dcbba5cc4996a15241ae3d3673dbc2a835387eb8b18bcf370613f6df72e0b3ddd6aaeceef1c682b2e777a082421d08bb122849acce1a8900f7307e0c302d32d1553ce31739d8ec4fe56" +
            "4c9184b8198bcf8e4662e65391b454cb1506f7d97f3632f8c2c5017ea656dc87b941addb86d2c49c49d4690207692fd0242fd51efdb65a0c0ef245b5860691e99915d74ab0f9cdb2721bc1e4f1b099d9bf" +
            "c6f3a0d88e304402205617000b702fcfdebf5a206dde2d3c2748c5b0c8dcb7ee4622253613dd70a30d022012e0891123de9c33cb50a25411cdc12d66a97c3d53cb4bb22d143129f8ffd729";

    private static String pyBlockKey = "cf8088acdd995aad6f5dcad8b99df5dcc088bac9ff8468f85b3c279543f9d297";
    private static String pyDoubleEntry = "190000000001000000000000006c7562759a9999999999e13f";

    @Test
    public void checkEncoding() throws Exception {
        Random rand = new Random();
        byte[] key = new byte[32];
        int keyVersion = 3;
        byte[] policyTag = new byte[32];
        byte[] encData = new byte[345];
        byte[] gcmTag = new byte[16];
        byte[] signature = new byte[72];
        rand.nextBytes(key);
        rand.nextBytes(policyTag);
        rand.nextBytes(encData);
        rand.nextBytes(gcmTag);
        rand.nextBytes(signature);

        CloudChunk chunk = new CloudChunk(key, keyVersion, policyTag, encData, gcmTag, signature);
        byte[] encoded = chunk.encode();
        CloudChunk after = CloudChunk.createCloudChunkFromByteString(encoded);
        assertArrayEquals(chunk.key, after.key);
        assertArrayEquals(chunk.gcmTag, after.gcmTag);
        assertArrayEquals(chunk.policyTag, after.policyTag);
        assertArrayEquals(chunk.encData, after.encData);
        assertArrayEquals(chunk.gcmTag, after.gcmTag);
        assertArrayEquals(chunk.signature, after.signature);
    }

    @Test
    public void checkEncodingPy() throws Exception {
        byte[] encoded = hexStringToByteArray(pyEncoded);
        CloudChunk after = CloudChunk.createCloudChunkFromByteString(encoded);
        assertEquals(1, after.keyVersion);
        assertEquals(pyEncoded, bytesToHexString(after.encode()));
    }

    @Test
    public void checkBlockIdGen() throws Exception {
        StreamIdentifier ident = new StreamIdentifier("lubu", 1, new byte[1], "lubu");
        assertEquals(pyBlockKey, Util.bytesToHexString(ident.getKeyForBlockId(0)));
    }


    @Test
    public void checkSign() throws Exception {
        Random rand = new Random();
        byte[] key = new byte[32];
        int keyVersion = 3;
        byte[] policyTag = new byte[32];
        byte[] encData = new byte[345];
        byte[] gcmTag = new byte[16];
        byte[] signature = new byte[72];
        rand.nextBytes(key);
        rand.nextBytes(policyTag);
        rand.nextBytes(encData);
        rand.nextBytes(gcmTag);
        rand.nextBytes(signature);
        KeyPair pair = StorageCrypto.generateECDSAKeys();

        CloudChunk chunk = new CloudChunk(key, keyVersion, policyTag, encData, gcmTag, pair.getPrivate());
        assertTrue(chunk.checkSignature(pair.getPublic()));

        chunk.key[3] = 0;
        chunk.key[6] = 0;

        assertFalse(chunk.checkSignature(pair.getPublic()));
    }

    @Test
    public void testEntry() throws Exception {
        DoubleEntry entry = new DoubleEntry(System.currentTimeMillis(), "hello", 1.556);
        byte[] data = entry.encode();
        DoubleEntry after = (DoubleEntry) (new DoubleEntry.DoubleEntryDecoder()).decode(data);
        assertEquals(entry.getTimestamp(), after.getTimestamp());
        assertEquals(entry.getMetadata(), after.getMetadata());
        assertEquals(entry.getDataValue(), after.getDataValue());
    }

    @Test
    public void testEntryPy() throws Exception {
        byte[] data = Util.hexStringToByteArray(pyDoubleEntry);
        DoubleEntry entry = (DoubleEntry) (new DoubleEntry.DoubleEntryDecoder()).decode(data);
        assertEquals(entry.getTimestamp(), 1);
        assertEquals(entry.getMetadata(), "lubu");
        assertEquals(String.valueOf(entry.getDataValue()), "0.55");
    }





}
