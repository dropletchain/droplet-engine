package ch.lubu.test;

import ch.lubu.Chunk;
import ch.lubu.ChunkKey;
import ch.lubu.Entry;
import ch.lubu.KademliaByteContent;
import ch.lubu.fitbitdata.FitbitCSVDataImporter;
import kademlia.JKademliaNode;
import kademlia.dht.GetParameter;
import kademlia.dht.KademliaStorageEntry;
import kademlia.exceptions.ContentNotFoundException;
import kademlia.node.KademliaId;
import org.junit.Test;

import java.io.IOException;
import java.util.List;
import java.util.Random;
import java.util.zip.DataFormatException;
import java.io.File;

/**
 * Created by lukas on 24.02.17.
 */
public class TestCompress {

    @Test
    public void testBlock() {
        Chunk chunk = Chunk.getNewBlock(10);
        chunk.putIotData(new Entry(1,"STEP", 10.0));
        chunk.putIotData(new Entry(2,"STEP", 12.0));
        chunk.putIotData(new Entry(3,"STEP", 14.0));
        byte[] compressed = chunk.getCompressedData();
        try {
            Chunk after = Chunk.getBlockFromCompressed(compressed);
            for(Entry entry : after)
                System.out.println(entry.getTimestamp() + " " + entry.getMetadata() + " " + entry.getValue());
        } catch (DataFormatException e) {
            e.printStackTrace();
        }

        System.out.println( (double) chunk.getData().length / (double) chunk.getCompressedData().length + " factor");
    }


    @Test
    public void testWithKademlia() {
        Chunk chunk = Chunk.getNewBlock(10);
        chunk.putIotData(new Entry(1,"STEP", 10.0));
        chunk.putIotData(new Entry(2,"STEP", 12.0));
        chunk.putIotData(new Entry(3,"STEP", 14.0));

        ChunkKey key = new ChunkKey("Lukas", "StreamTest", 1);
        try {
            JKademliaNode node1;
            node1 = new JKademliaNode("node 1", new KademliaId(), 12067);
            JKademliaNode node2 = new JKademliaNode("node 2", new KademliaId(), 12068);
            node2.bootstrap(node1.getNode());

            System.out.println("NodeID1 " + node1.getNode().getNodeId().hexRepresentation());
            System.out.println("NodeID2 " + node2.getNode().getNodeId().hexRepresentation());


            KademliaByteContent byteContent = new KademliaByteContent(key.getKademliaKey(), "Lukas", chunk.getCompressedData());
            node2.put(byteContent);


            System.out.println("Retrieving Content");
            GetParameter gp = new GetParameter(key.getKademliaKey(), byteContent.getType());
            gp.setOwnerId("Lukas");
            System.out.println("Get Parameter: " + gp);
            KademliaStorageEntry content = node1.get(gp);

            System.out.println("Content Found: " + new String(content.getContent()));
            System.out.println("Content Metadata: " + content.getContentMetadata());

            KademliaByteContent out = KademliaByteContent.createFromBytes(content.getContent());

            Chunk outChunk = Chunk.getBlockFromCompressed(out.getData());

            for(Entry entry : outChunk)
                System.out.println(entry.getTimestamp() + " " + entry.getMetadata() + " " + entry.getValue());


            Thread.sleep(10000);
            node1.shutdown(false);
            node2.shutdown(false);

        } catch (IOException e) {
            e.printStackTrace();
        } catch (ContentNotFoundException e) {
            e.printStackTrace();
        } catch (InterruptedException e) {
            e.printStackTrace();
        } catch (DataFormatException e) {
            e.printStackTrace();
        }
    }

    @Test
    public void testDHT() {
        int num_server = 20;
        JKademliaNode[] nodes = new JKademliaNode[num_server];
        Random rand = new Random();

        Chunk chunk = Chunk.getNewBlock(10);
        chunk.putIotData(new Entry(1,"STEP", 10.0));
        chunk.putIotData(new Entry(2,"STEP", 12.0));
        chunk.putIotData(new Entry(3,"STEP", 14.0));
        ChunkKey key = new ChunkKey("Lukas", "StreamTest", 1);

        try {
            for (int i = 0; i < num_server; i++) {
                nodes[i] = new JKademliaNode("node" + i, new KademliaId(), 12066 + i);
                System.out.println("NodeID"  +i + nodes[i].getNode().getNodeId().hexRepresentation());
            }

            for (int i = 1; i < num_server; i++) {
                nodes[i].bootstrap(nodes[i-1].getNode());
                Thread.sleep(100);

            }

            Thread.sleep(1000);

            /*for (int i = 0; i < num_server; i++) {
                int tmp = rand.nextInt();
                try {
                    nodes[i].bootstrap(nodes[(tmp < 0 ? -tmp : tmp) % num_server].getNode());
                } catch (RoutingException e) {

                }
            }*/

            KademliaByteContent byteContent = new KademliaByteContent(key.getKademliaKey(), "Lukas", chunk.getCompressedData());
            nodes[0].put(byteContent);

            GetParameter gp = new GetParameter(key.getKademliaKey(), byteContent.getType());
            gp.setOwnerId("Lukas");
            KademliaStorageEntry content = nodes[num_server-1].get(gp);

            KademliaByteContent out = KademliaByteContent.createFromBytes(content.getContent());

            Chunk outChunk = Chunk.getBlockFromCompressed(out.getData());

            for(Entry entry : outChunk)
                System.out.println(entry.getTimestamp() + " " + entry.getMetadata() + " " + entry.getValue());

            Thread.sleep(1000);

            for (int i = 0; i < num_server; i++) {
                nodes[i].shutdown(false);
            }

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @Test
    public void testAvaBlocks() {
        File data = new File("./../../raw-data/FitBit/fitbit_export_20161201.csv");
        List<Entry> entries = FitbitCSVDataImporter.importCSVData(data);
        System.out.format("%d\n", entries.size());
    }

}
