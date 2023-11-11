import logging
import serial
import time


class SerialConnection:
    """Interface for communicating with the TinyK through a serial connection.
    """
    def send(self, data: bytes) -> None:
        """Sends the data.

        Args:
            data (bytes): the data.
        """
        pass

    def read(self) -> bytes:
        """Reads the data.

        Returns:
            bytes: the data.
        """
        pass

    def has_data_to_be_read(self) -> bool:
        """Signals whether there is data to be read.

        Returns:
            bool: True if there's data to be read.
        """
        pass

    def reconnect(self) -> None:
        """Reconnects in case of failure.
        """
        pass

class UART(SerialConnection):
    """Represents a UART serial connection.

    Args:
        SerialConnection ([type]): the superclass.

    Returns:
        [type]: UART.
    """
    MAX_RETRIES: int = 10

    def __init__(
        self, port: int, baud_rate: int, write_timeout: int, read_timeout: int
    ) -> None:
        """Creates a new instance.

        Args:
            port (int): the port to use.
            baud_rate (int): the baud rate.
            write_timeout (int): the timeout for writing.
            read_timeout (int): the timeout for reading.
        """
        self.port = port
        self.baud_rate = baud_rate
        self.write_timeout = write_timeout
        self.read_timeout = read_timeout
        logging.info(
            f"init UART: port {port}, baud_rate: {baud_rate}, write_timeout: {write_timeout}, read_timeout: {read_timeout}"
        )
        self.reconnect()

    def send(self, data: bytes) -> None:
        count: int = 0
        logging.info(f"send data: {data}")
        while count < UART.MAX_RETRIES:
            try:
                self.connection.flushInput()
                self.connection.flushOutput()
                time.sleep(0.1)
                self.connection.write(data)
                logging.info(f"connection write: {data}")
                break
            except KeyboardInterrupt:
                raise
            except Exception:
                self.reconnect()
                count += 1
                if count == UART.MAX_RETRIES:
                    raise

    def has_data_to_be_read(self) -> bool:
        return self.connection.inWaiting() > 0

    def read(self, size: int = 1) -> bytes:
        count: int = 0
        while count < UART.MAX_RETRIES:
            try:
                time.sleep(0.1)
                return self.connection.read(size)
            except KeyboardInterrupt:
                raise
            except Exception:
                self.reconnect()
                count += 1
                if count == UART.MAX_RETRIES:
                    raise

    def reconnect(self) -> None:
        logging.info("UART - reconnecting")
        try:
            self.connection.close()
        except KeyboardInterrupt:
            raise
        except Exception:
            pass

        self.connection = serial.Serial(
            self.port,
            self.baud_rate,
            write_timeout=self.write_timeout,
            timeout=self.read_timeout,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        time.sleep(0.2)
        self.connection.flushInput()
        self.connection.flushOutput()
        time.sleep(0.1)

class DummyUART(SerialConnection):
    """Pseudo-UART for testing purposes.

    Args:
        SerialConnection ([type]): the superclass.
    """
    def send(self, data: bytes) -> None:
        logging.debug("DummyUart send: {}".format(data))

    def read(self, size: int = 1) -> bytes:
        logging.debug("DummyUart read")
        return b"\n"

    def has_data_to_be_read(self) -> bool:
        return True


class FakeUART(SerialConnection):
    """
    Returns messages with predefined responses.
    """

    def __init__(self, read_responses: bytes):
        self.read_responses: bytes = read_responses
        self.read_index = 0

    def send(self, data: bytes) -> None:
        logging.debug(f"FakeUart send: {data}")

    def read(self, size: int = 1) -> bytes:
        logging.debug(f"FakeUart - read with size: {size}")
        data = self.read_responses[self.read_index : (self.read_index + size)]
        logging.debug(f"FakeUart - read data: {data} with size: {size}")

        self.read_index += size

        return data

    def has_data_to_be_read(self) -> bool:
        return True
