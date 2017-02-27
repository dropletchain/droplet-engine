package ch.lubu;

/**
 * Created by lukas on 27.02.17.
 */
public class BlockVerficationFailure extends Exception {

    private byte[] data;

    public BlockVerficationFailure(String message, byte[] block) {
        super(message);
        this.data = data;
    }

    public byte[] getBlock() {
        return data;
    }
}
